from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.urls import reverse


def build_booking_payload(booking):
    return {
        'id': booking.id,
        'customer_id': booking.customer_id,
        'customer_username': booking.customer.username,
        'vehicle_id': booking.vehicle_id,
        'vehicle_label': f'{booking.vehicle.make} {booking.vehicle.model}',
        'vehicle_plate': booking.vehicle.license_plate,
        'route_id': booking.route_id,
        'route_origin': booking.route.origin,
        'route_destination': booking.route.destination,
        'travel_date': booking.travel_date.isoformat(),
        'seat_numbers': booking.seat_numbers,
        'seats_booked': booking.seats_booked,
        'total_price': str(booking.total_price),
        'status': booking.status,
        'receipt_url': reverse('booking-receipt', kwargs={'pk': booking.pk}),
        'payment_proof_url': booking.payment_proof.url if booking.payment_proof else '',
    }


def broadcast_booking_event(event_type, booking):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    async_to_sync(channel_layer.group_send)(
        'dispatcher',
        {
            'type': event_type,
            'booking': build_booking_payload(booking),
        },
    )


def build_parcel_payload(parcel):
    route_label = ''
    if parcel.route_id:
        route_label = f'{parcel.route.origin} to {parcel.route.destination}'

    return {
        'id': parcel.id,
        'tracking_code': parcel.tracking_code,
        'customer_id': parcel.customer_id,
        'route_id': parcel.route_id,
        'route_label': route_label,
        'status': parcel.status,
        'status_display': parcel.get_status_display(),
        'current_location': parcel.current_location,
        'expected_delivery_date': parcel.expected_delivery_date.isoformat() if parcel.expected_delivery_date else '',
        'updated_at': parcel.updated_at.isoformat(),
    }


def broadcast_parcel_event(event_type, parcel):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    async_to_sync(channel_layer.group_send)(
        'dispatcher',
        {
            'type': event_type,
            'parcel': build_parcel_payload(parcel),
        },
    )