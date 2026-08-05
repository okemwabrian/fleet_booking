from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_POST
import logging

import json

from bookings.models import Booking, ParcelShipment
from bookings.notifications import send_booking_approval_email, send_booking_approval_sms
from bookings.realtime import broadcast_booking_event, broadcast_parcel_event
from bookings.tracking import log_parcel_tracking_event
from messaging.models import Message
from profiles.models import UserProfile
from routes.models import Route
from vehicles.models import Vehicle

from .forms import (
    AdminBookingForm,
    AdminParcelForm,
    AdminRouteForm,
    AdminVehicleForm,
    CustomerLoginForm,
    CustomerSignUpForm,
    ParcelCreateForm,
    ParcelTrackingLookupForm,
    ProfileUpdateForm,
    RouteSearchForm,
)


logger = logging.getLogger(__name__)


def _normalize_form_errors(form):
    normalized = {}
    for field, errors in form.errors.items():
        normalized[field] = [str(error) for error in errors]
    return normalized


def home(request):
    form = RouteSearchForm()
    featured_routes = Route.objects.filter(is_active=True).order_by('origin', 'destination')[:6]
    return render(
        request,
        'home.html',
        {
            'search_form': form,
            'featured_routes': featured_routes,
        },
    )


def search_results(request):
    form = RouteSearchForm(request.GET or None)
    route_cards = []
    travel_date = None
    user_phone = ''

    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        user_phone = profile.phone_number or ''

    if form.is_valid():
        origin = form.cleaned_data['origin']
        destination = form.cleaned_data['destination']
        travel_date = form.cleaned_data['travel_date']

        matching_routes = Route.objects.filter(
            is_active=True,
            origin__icontains=origin,
            destination__icontains=destination,
        ).order_by('origin', 'destination')

        active_vehicles = Vehicle.objects.filter(status='AVAILABLE').order_by('make', 'model')

        for route in matching_routes:
            vehicle_options = []
            for vehicle in active_vehicles:
                existing_bookings = Booking.objects.filter(
                    vehicle=vehicle,
                    travel_date=travel_date,
                ).exclude(status='CANCELLED')

                seats_booked = existing_bookings.aggregate(total=Sum('seats_booked'))['total'] or 0
                booked_seat_numbers = []
                for existing_booking in existing_bookings.only('seat_numbers'):
                    if isinstance(existing_booking.seat_numbers, list):
                        booked_seat_numbers.extend(existing_booking.seat_numbers)

                # Keep deterministic order and uniqueness for template rendering.
                booked_seat_numbers = sorted(set(booked_seat_numbers))

                seats_remaining = vehicle.capacity - seats_booked
                if seats_remaining > 0:
                    vehicle_options.append(
                        {
                            'vehicle': vehicle,
                            'seats_remaining': seats_remaining,
                            'booked_seat_numbers': booked_seat_numbers,
                        }
                    )

            if vehicle_options:
                route_cards.append(
                    {
                        'route': route,
                        'vehicle_options': vehicle_options,
                    }
                )

    return render(
        request,
        'search_results.html',
        {
            'search_form': form,
            'route_cards': route_cards,
            'travel_date': travel_date,
            'user_phone': user_phone,
        },
    )


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Your account is ready. Welcome aboard.')
            return redirect('dashboard')
    else:
        form = CustomerSignUpForm()

    return render(request, 'registration/signup.html', {'form': form})


@require_POST
def ajax_login(request):
    username = (request.POST.get('username') or '').strip()
    password = request.POST.get('password') or ''

    user = authenticate(request, username=username, password=password)
    if not user:
        return JsonResponse(
            {
                'ok': False,
                'errors': {
                    '__all__': ['Invalid username or password.'],
                },
            },
            status=400,
        )

    login(request, user)
    return JsonResponse({'ok': True, 'user': {'id': user.id, 'username': user.username}})


@require_POST
def ajax_register(request):
    form = CustomerSignUpForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'ok': False, 'errors': _normalize_form_errors(form)}, status=400)

    user = form.save()
    login(request, user)
    return JsonResponse({'ok': True, 'user': {'id': user.id, 'username': user.username}})


class CustomerLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = CustomerLoginForm


class CustomerLogoutView(LogoutView):
    next_page = reverse_lazy('home')


@login_required
def dashboard(request):
    if request.user.is_staff:
        return redirect('admin-dashboard')
    return redirect('user-dashboard')


@login_required
def user_dashboard(request):
    bookings = Booking.objects.select_related('vehicle', 'route', 'customer').filter(
        customer=request.user
    ).order_by('-travel_date', '-created_at')
    parcels = (
        ParcelShipment.objects.select_related('route')
        .prefetch_related('tracking_events')
        .filter(customer=request.user)
        .order_by('-created_at')
    )

    booking_counts = {
        'total': bookings.count(),
        'pending': bookings.filter(status='PENDING').count(),
        'approved': bookings.filter(status='APPROVED').count(),
        'completed': bookings.filter(status='COMPLETED').count(),
    }

    transaction_totals = {
        'bookings_amount': sum(float(booking.total_price or 0) for booking in bookings),
        'parcel_amount': sum(float(parcel.fee or 0) for parcel in parcels),
    }
    transaction_totals['grand_total'] = transaction_totals['bookings_amount'] + transaction_totals['parcel_amount']

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    contacts_qs = User.objects.filter(is_staff=True).order_by('username')

    contacts = list(contacts_qs)
    selected_contact = None
    selected_contact_id = request.GET.get('contact')
    if selected_contact_id:
        selected_contact = next((contact for contact in contacts if str(contact.pk) == str(selected_contact_id)), None)
    if not selected_contact and contacts:
        selected_contact = contacts[0]

    unread_counts = {}
    unread_queryset = Message.objects.filter(receiver=request.user, is_read=False).values('sender_id')
    for row in unread_queryset:
        sender_id = str(row['sender_id'])
        unread_counts[sender_id] = unread_counts.get(sender_id, 0) + 1

    thread_messages = []
    if selected_contact:
        Message.objects.filter(sender=selected_contact, receiver=request.user, is_read=False).update(is_read=True)
        unread_counts[str(selected_contact.id)] = 0

        thread_queryset = Message.objects.filter(
            sender_id__in=[request.user.id, selected_contact.id],
            receiver_id__in=[request.user.id, selected_contact.id],
        ).select_related('sender', 'receiver').order_by('-created_at')[:40]
        thread_messages = list(reversed(thread_queryset))

    return render(
        request,
        'dashboard.html',
        {
            'bookings': bookings,
            'booking_counts': booking_counts,
            'profile': profile,
            'profile_form': ProfileUpdateForm(instance=profile),
            'parcel_form': ParcelCreateForm(),
            'parcels': parcels,
            'transaction_totals': transaction_totals,
            'chat_contacts': contacts,
            'selected_contact': selected_contact,
            'thread_messages': thread_messages,
            'unread_counts': unread_counts,
            'unread_counts_json': json.dumps(unread_counts),
        },
    )


@staff_member_required
def admin_dashboard(request):
    pending_bookings = Booking.objects.select_related('customer', 'route', 'vehicle').filter(status='PENDING').order_by('-created_at')[:8]
    active_parcels = ParcelShipment.objects.select_related('customer', 'route').exclude(status=ParcelShipment.STATUS_DELIVERED).order_by('-updated_at')[:8]

    return render(
        request,
        'admin/dashboard.html',
        {
            'pending_bookings': pending_bookings,
            'active_parcels': active_parcels,
            'booking_counts': {
                'pending': Booking.objects.filter(status='PENDING').count(),
                'approved': Booking.objects.filter(status='APPROVED').count(),
                'completed': Booking.objects.filter(status='COMPLETED').count(),
            },
            'parcel_counts': {
                'in_transit': ParcelShipment.objects.filter(status=ParcelShipment.STATUS_IN_TRANSIT).count(),
                'arrived': ParcelShipment.objects.filter(status=ParcelShipment.STATUS_ARRIVED).count(),
                'delivered': ParcelShipment.objects.filter(status=ParcelShipment.STATUS_DELIVERED).count(),
            },
        },
    )


@login_required
def update_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method != 'POST':
        return redirect('dashboard')

    form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
    if form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully.')
    else:
        messages.error(request, 'Unable to update profile. Please correct the highlighted values.')
    return redirect('dashboard')


@login_required
@require_POST
def update_theme_preference(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'Invalid JSON payload.'}, status=400)

    theme = (payload.get('theme') or '').strip().lower()
    if theme not in {'light', 'dark', 'system'}:
        return JsonResponse({'ok': False, 'error': 'Theme must be light, dark, or system.'}, status=400)

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.theme_preference = theme
    profile.save(update_fields=['theme_preference', 'updated_at'])
    return JsonResponse({'ok': True, 'theme': theme})


@staff_member_required
def command_center(request):
    active_tab = request.GET.get('tab', 'bookings').strip().lower()
    if active_tab not in {'bookings', 'vehicles', 'routes', 'parcels'}:
        active_tab = 'bookings'

    status_filter = request.GET.get('status', '').strip()
    bookings = Booking.objects.select_related('customer', 'route', 'vehicle').order_by('-created_at')
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    vehicles = Vehicle.objects.order_by('make', 'model', 'license_plate')
    routes = Route.objects.order_by('origin', 'destination')
    parcels = ParcelShipment.objects.select_related('customer', 'route').order_by('-created_at')

    return render(
        request,
        'admin/command_center.html',
        {
            'active_tab': active_tab,
            'bookings': bookings,
            'vehicles': vehicles,
            'routes': routes,
            'parcels': parcels,
            'status_filter': status_filter,
            'create_booking_form': AdminBookingForm(),
            'create_vehicle_form': AdminVehicleForm(),
            'create_route_form': AdminRouteForm(),
            'create_parcel_form': AdminParcelForm(),
            'status_choices': Booking.STATUS_CHOICES,
            'parcel_status_choices': ParcelShipment.STATUS_CHOICES,
        },
    )


def _generate_tracking_code():
    for _ in range(10):
        code = f"FBP{get_random_string(8, allowed_chars='ABCDEFGHJKLMNPQRSTUVWXYZ23456789')}"
        if not ParcelShipment.objects.filter(tracking_code=code).exists():
            return code
    return f"FBP{get_random_string(10).upper()}"


def _notify_booking_approval_if_needed(booking, previous_status):
    if booking.status != 'APPROVED' or previous_status == 'APPROVED':
        return False

    try:
        emailed = send_booking_approval_email(booking)
    except Exception:
        logger.exception('Failed to send booking approval email for booking %s', booking.pk)
        emailed = False

    sms_sent = send_booking_approval_sms(booking)
    return emailed or sms_sent


def _build_parcel_update_note(previous_status, new_status, previous_location, new_location, manual_note=''):
    changes = []
    if previous_status != new_status:
        changes.append(f'Status updated from {previous_status} to {new_status}.')
    if (previous_location or '').strip() != (new_location or '').strip():
        from_label = (previous_location or 'Unknown location').strip()
        to_label = (new_location or 'Unknown location').strip()
        changes.append(f'Location moved from {from_label} to {to_label}.')
    if manual_note:
        changes.append(manual_note.strip())
    return ' '.join(changes).strip()


@login_required
@require_POST
def create_parcel_shipment(request):
    form = ParcelCreateForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Parcel request failed. Please review the sender and receiver details.')
        return redirect('user-dashboard')

    parcel = form.save(commit=False)
    parcel.customer = request.user
    parcel.tracking_code = _generate_tracking_code()
    base_fee = float(parcel.route.base_price) if parcel.route else 0.0
    weight = float(parcel.weight_kg or 1)
    parcel.fee = round(max(base_fee * 0.35, 250.0) + (weight * 40.0), 2)
    if not parcel.current_location:
        parcel.current_location = parcel.route.origin if parcel.route else 'Received at booking office'
    parcel.save()
    log_parcel_tracking_event(parcel=parcel, created_by=request.user, note='Shipment request submitted.')
    broadcast_parcel_event('parcel.created', parcel)

    messages.success(request, f'Parcel submitted successfully. Tracking code: {parcel.tracking_code}.')
    return redirect('user-dashboard')


@staff_member_required
@require_POST
def command_center_update_booking_status(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    status_value = (request.POST.get('status') or '').strip().upper()
    valid_statuses = {choice[0] for choice in Booking.STATUS_CHOICES}

    if status_value not in valid_statuses:
        messages.error(request, 'Invalid booking status selected.')
        return redirect(f"{reverse_lazy('command-center')}?tab=bookings")

    previous_status = booking.status
    booking.status = status_value
    booking.save(update_fields=['status'])
    notifications_sent = _notify_booking_approval_if_needed(booking, previous_status)

    if booking.status != previous_status:
        broadcast_booking_event('booking.updated', booking)
    if notifications_sent:
        messages.success(request, f'Booking #{booking.pk} status updated to {booking.get_status_display()}. Receipt notifications sent.')
    else:
        messages.success(request, f'Booking #{booking.pk} status updated to {booking.get_status_display()}.')
    return redirect(f"{reverse_lazy('command-center')}?tab=bookings")


@staff_member_required
def command_center_create_parcel(request):
    if request.method != 'POST':
        return redirect(f"{reverse_lazy('command-center')}?tab=parcels")

    form = AdminParcelForm(request.POST)
    if form.is_valid():
        parcel = form.save(commit=False)
        if not parcel.customer_id:
            parcel.customer = request.user
        if not parcel.tracking_code:
            parcel.tracking_code = _generate_tracking_code()
        parcel.save()
        log_parcel_tracking_event(parcel=parcel, created_by=request.user, note='Shipment record created by dispatcher.')
        broadcast_parcel_event('parcel.created', parcel)
        messages.success(request, f'Parcel {parcel.tracking_code} created successfully.')
    else:
        messages.error(request, 'Parcel creation failed. Please review form values.')
    return redirect(f"{reverse_lazy('command-center')}?tab=parcels")


@staff_member_required
def command_center_edit_parcel(request, pk):
    parcel = get_object_or_404(ParcelShipment, pk=pk)
    previous_status_code = parcel.status
    previous_status = parcel.get_status_display()
    previous_location = parcel.current_location

    if request.method == 'POST':
        form = AdminParcelForm(request.POST, instance=parcel)
        if form.is_valid():
            updated_parcel = form.save()
            note = _build_parcel_update_note(
                previous_status=previous_status,
                new_status=updated_parcel.get_status_display(),
                previous_location=previous_location,
                new_location=updated_parcel.current_location,
                manual_note=request.POST.get('update_note', ''),
            )
            if note:
                log_parcel_tracking_event(parcel=updated_parcel, created_by=request.user, note=note)
            if (
                updated_parcel.status != previous_status_code
                or (updated_parcel.current_location or '').strip() != (previous_location or '').strip()
            ):
                broadcast_parcel_event('parcel.updated', updated_parcel)
            messages.success(request, f'Parcel {parcel.tracking_code} updated successfully.')
            return redirect(f"{reverse_lazy('command-center')}?tab=parcels")
        messages.error(request, 'Parcel update failed. Please fix the form errors.')
    else:
        form = AdminParcelForm(instance=parcel)

    return render(
        request,
        'admin/parcel_edit.html',
        {
            'parcel': parcel,
            'form': form,
            'recent_events': parcel.tracking_events.select_related('created_by')[:10],
        },
    )


@staff_member_required
def command_center_delete_parcel(request, pk):
    if request.method != 'POST':
        return redirect(f"{reverse_lazy('command-center')}?tab=parcels")

    parcel = get_object_or_404(ParcelShipment, pk=pk)
    code = parcel.tracking_code
    parcel.delete()
    messages.success(request, f'Parcel {code} deleted.')
    return redirect(f"{reverse_lazy('command-center')}?tab=parcels")


@staff_member_required
def command_center_create_booking(request):
    if request.method != 'POST':
        return redirect('command-center')

    form = AdminBookingForm(request.POST, request.FILES)
    if form.is_valid():
        booking = form.save()
        _notify_booking_approval_if_needed(booking, previous_status='')
        broadcast_booking_event('booking.created', booking)
        messages.success(request, 'Booking created successfully from command center.')
    else:
        messages.error(request, 'Booking creation failed. Please review the form fields.')
    return redirect(f"{reverse_lazy('command-center')}?tab=bookings")


@staff_member_required
def command_center_edit_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    previous_status = booking.status

    if request.method == 'POST':
        form = AdminBookingForm(request.POST, request.FILES, instance=booking)
        if form.is_valid():
            updated_booking = form.save()
            _notify_booking_approval_if_needed(updated_booking, previous_status)
            if updated_booking.status != previous_status:
                broadcast_booking_event('booking.updated', updated_booking)
            messages.success(request, f'Booking #{booking.pk} updated successfully.')
            return redirect(f"{reverse_lazy('command-center')}?tab=bookings")
        messages.error(request, 'Booking update failed. Please fix the form errors.')
    else:
        form = AdminBookingForm(instance=booking)

    return render(
        request,
        'admin/booking_edit.html',
        {
            'booking': booking,
            'form': form,
        },
    )


@staff_member_required
def command_center_delete_booking(request, pk):
    if request.method != 'POST':
        return redirect('command-center')

    booking = get_object_or_404(Booking, pk=pk)
    booking.delete()
    messages.success(request, f'Booking #{pk} deleted.')
    return redirect(f"{reverse_lazy('command-center')}?tab=bookings")


@staff_member_required
def command_center_create_vehicle(request):
    if request.method != 'POST':
        return redirect(f"{reverse_lazy('command-center')}?tab=vehicles")

    form = AdminVehicleForm(request.POST)
    if form.is_valid():
        vehicle = form.save()
        messages.success(request, f'Vehicle {vehicle.license_plate} created successfully.')
    else:
        messages.error(request, 'Vehicle creation failed. Please review the form fields.')
    return redirect(f"{reverse_lazy('command-center')}?tab=vehicles")


@staff_member_required
def command_center_edit_vehicle(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)

    if request.method == 'POST':
        form = AdminVehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, f'Vehicle {vehicle.license_plate} updated successfully.')
            return redirect(f"{reverse_lazy('command-center')}?tab=vehicles")
        messages.error(request, 'Vehicle update failed. Please fix the form errors.')
    else:
        form = AdminVehicleForm(instance=vehicle)

    return render(
        request,
        'admin/vehicle_edit.html',
        {
            'vehicle': vehicle,
            'form': form,
        },
    )


@staff_member_required
def command_center_delete_vehicle(request, pk):
    if request.method != 'POST':
        return redirect(f"{reverse_lazy('command-center')}?tab=vehicles")

    vehicle = get_object_or_404(Vehicle, pk=pk)
    plate = vehicle.license_plate
    vehicle.delete()
    messages.success(request, f'Vehicle {plate} deleted.')
    return redirect(f"{reverse_lazy('command-center')}?tab=vehicles")


@staff_member_required
def command_center_create_route(request):
    if request.method != 'POST':
        return redirect(f"{reverse_lazy('command-center')}?tab=routes")

    form = AdminRouteForm(request.POST)
    if form.is_valid():
        route = form.save()
        messages.success(request, f'Route {route.origin} to {route.destination} created successfully.')
    else:
        messages.error(request, 'Route creation failed. Please review the form fields.')
    return redirect(f"{reverse_lazy('command-center')}?tab=routes")


@staff_member_required
def command_center_edit_route(request, pk):
    route = get_object_or_404(Route, pk=pk)

    if request.method == 'POST':
        form = AdminRouteForm(request.POST, instance=route)
        if form.is_valid():
            form.save()
            messages.success(request, f'Route {route.origin} to {route.destination} updated successfully.')
            return redirect(f"{reverse_lazy('command-center')}?tab=routes")
        messages.error(request, 'Route update failed. Please fix the form errors.')
    else:
        form = AdminRouteForm(instance=route)

    return render(
        request,
        'admin/route_edit.html',
        {
            'route': route,
            'form': form,
        },
    )


@staff_member_required
def command_center_delete_route(request, pk):
    if request.method != 'POST':
        return redirect(f"{reverse_lazy('command-center')}?tab=routes")

    route = get_object_or_404(Route, pk=pk)
    label = f'{route.origin} to {route.destination}'
    route.delete()
    messages.success(request, f'Route {label} deleted.')
    return redirect(f"{reverse_lazy('command-center')}?tab=routes")


def public_track_parcel(request):
    form = ParcelTrackingLookupForm(request.GET or None)
    parcel = None

    if request.GET.get('tracking_code') and form.is_valid():
        tracking_code = form.cleaned_data['tracking_code']
        parcel = (
            ParcelShipment.objects.select_related('route')
            .prefetch_related('tracking_events__created_by')
            .filter(tracking_code__iexact=tracking_code)
            .first()
        )
        if not parcel:
            messages.error(request, f'No parcel found for tracking code {tracking_code}.')

    return render(
        request,
        'track.html',
        {
            'tracking_form': form,
            'tracked_parcel': parcel,
        },
    )