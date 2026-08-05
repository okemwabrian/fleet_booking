from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import HttpResponse
from .models import Booking
from .serializers import BookingSerializer
from .receipts import build_booking_receipt_pdf


def _format_serializer_errors(serializer_errors):
    messages_list = []

    for field, errors in serializer_errors.items():
        if isinstance(errors, (list, tuple)):
            for error in errors:
                if field == 'seat_numbers' and 'already booked' in str(error).lower():
                    messages_list.append(f'Sorry, {error}')
                elif field == 'non_field_errors':
                    messages_list.append(str(error))
                else:
                    messages_list.append(f'{field.replace("_", " ").title()}: {error}')
        else:
            messages_list.append(f'{field.replace("_", " ").title()}: {errors}')

    return ' '.join(messages_list) if messages_list else 'Unable to create booking. Please check the available seats and try again.'

class BookingListCreateAPIView(APIView):
    """
    List all bookings, or create a new booking.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookings = Booking.objects.select_related('customer', 'vehicle', 'route').order_by('-created_at')
        if not request.user.is_staff:
            bookings = bookings.filter(customer=request.user)
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BookingSerializer(data=request.data)
        if serializer.is_valid():
            booking = serializer.save(customer=request.user)
            receipt_url = request.build_absolute_uri(reverse('booking-receipt', kwargs={'pk': booking.pk}))
            if request.accepted_renderer.format == 'json':
                return Response(
                    {
                        'booking': BookingSerializer(booking).data,
                        'receipt_url': receipt_url,
                    },
                    status=status.HTTP_201_CREATED,
                )
            messages.success(request, 'Booking submitted successfully. You can view your receipt from the dashboard history.')
            return redirect('dashboard')
        if request.accepted_renderer.format == 'json':
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        messages.error(request, _format_serializer_errors(serializer.errors))
        return redirect(request.META.get('HTTP_REFERER', reverse('search-results')))


class BookingReceiptView(LoginRequiredMixin, View):
    def get(self, request, pk):
        booking = get_object_or_404(
            Booking.objects.select_related('customer', 'vehicle', 'route'),
            pk=pk,
        )

        if not request.user.is_staff and booking.customer_id != request.user.id:
            return HttpResponse(status=403)

        pdf_bytes = build_booking_receipt_pdf(booking, request=request)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="booking-{booking.pk}-receipt.pdf"'
        return response