import json
import logging
from urllib import error, request as urllib_request

from django.conf import settings
from django.core.mail import EmailMessage

from bookings.receipts import build_booking_receipt_pdf

logger = logging.getLogger(__name__)


def send_booking_approval_email(booking):
    recipient = (booking.contact_email or booking.customer.email or '').strip()
    if not recipient:
        logger.info('Skipping booking approval email for booking %s: no recipient email.', booking.pk)
        return False

    route_label = 'Route not assigned'
    if booking.route_id:
        route_label = f'{booking.route.origin} to {booking.route.destination}'

    subject = f'Your Fleet Booking Ticket #{booking.pk} Is Approved'
    body = (
        f'Hello {booking.customer.get_full_name() or booking.customer.username},\n\n'
        'Your booking has been approved. Your PDF ticket is attached to this email.\n\n'
        f'Route: {route_label}\n'
        f'Travel date: {booking.travel_date}\n'
        f'Seats: {booking.seats_booked}\n'
        f'Total paid: KES {booking.total_price}\n\n'
        'Thank you for choosing Fleet Booking.'
    )

    pdf_bytes = build_booking_receipt_pdf(booking)
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@fleetbooking.local'),
        to=[recipient],
    )
    email.attach(f'booking-{booking.pk}-receipt.pdf', pdf_bytes, 'application/pdf')
    email.send(fail_silently=False)
    return True


def send_booking_approval_sms(booking):
    webhook_url = getattr(settings, 'SMS_WEBHOOK_URL', '').strip()
    recipient_phone = (booking.contact_phone or '').strip()

    if not webhook_url or not recipient_phone:
        return False

    route_label = 'route pending assignment'
    if booking.route_id:
        route_label = f'{booking.route.origin} to {booking.route.destination}'

    payload = {
        'event': 'booking_approved',
        'booking_id': booking.pk,
        'to': recipient_phone,
        'message': (
            f'Fleet Booking: Your booking #{booking.pk} is approved. '
            f'Route {route_label} on {booking.travel_date}. '
            'Your receipt has been sent via email.'
        ),
    }

    req = urllib_request.Request(
        webhook_url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )

    try:
        with urllib_request.urlopen(req, timeout=8) as response:
            return 200 <= response.status < 300
    except (error.URLError, TimeoutError) as exc:
        logger.warning('Booking approval SMS webhook failed for booking %s: %s', booking.pk, exc)
        return False
