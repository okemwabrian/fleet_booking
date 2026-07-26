from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'vehicle', 'route', 'travel_date', 'status', 'total_price')
    list_filter = ('status', 'travel_date')
    search_fields = ('customer__username', 'vehicle__license_plate', 'route__origin')