from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Booking, ParcelShipment, ParcelTrackingEvent

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'vehicle', 'route', 'travel_date', 'seats_booked', 'contact_phone', 'status', 'total_price', 'has_payment_proof', 'receipt_pdf')
    list_filter = ('status', 'travel_date')
    search_fields = ('customer__username', 'vehicle__license_plate', 'route__origin', 'contact_phone', 'contact_email')

    def receipt_pdf(self, obj):
        url = reverse('booking-receipt', kwargs={'pk': obj.pk})
        return format_html('<a href="{}" target="_blank">Download</a>', url)

    receipt_pdf.short_description = 'Receipt'

    def has_payment_proof(self, obj):
        return bool(obj.payment_proof)

    has_payment_proof.boolean = True
    has_payment_proof.short_description = 'Payment proof'


@admin.register(ParcelShipment)
class ParcelShipmentAdmin(admin.ModelAdmin):
    list_display = (
        'tracking_code',
        'customer',
        'route',
        'status',
        'current_location',
        'fee',
        'updated_at',
    )
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = (
        'tracking_code',
        'customer__username',
        'sender_name',
        'sender_phone',
        'receiver_name',
        'receiver_phone',
    )


@admin.register(ParcelTrackingEvent)
class ParcelTrackingEventAdmin(admin.ModelAdmin):
    list_display = ('parcel', 'status', 'location', 'created_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('parcel__tracking_code', 'location', 'note', 'created_by__username')