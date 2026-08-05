from bookings.models import ParcelTrackingEvent


def log_parcel_tracking_event(parcel, created_by=None, note=''):
    """Persist a timeline event for parcel status/location updates."""
    return ParcelTrackingEvent.objects.create(
        parcel=parcel,
        status=parcel.status,
        location=parcel.current_location or '',
        note=(note or '').strip(),
        created_by=created_by,
    )
