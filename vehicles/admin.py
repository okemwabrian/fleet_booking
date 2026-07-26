from django.contrib import admin
from .models import Vehicle

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    # Removed 'daily_rate' from the end of this list
    list_display = ('make', 'model', 'year', 'license_plate', 'status')
    list_filter = ('status', 'year')
    search_fields = ('make', 'model', 'license_plate')