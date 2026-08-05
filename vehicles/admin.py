from django.contrib import admin
from .models import Vehicle

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('make', 'model', 'year', 'license_plate', 'capacity', 'status')
    list_filter = ('status', 'year')
    search_fields = ('make', 'model', 'license_plate')