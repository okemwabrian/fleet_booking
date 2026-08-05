from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import your Views
from vehicles.views import VehicleViewSet
from routes.views import RouteViewSet
from bookings.views import BookingListCreateAPIView
from bookings.views import BookingReceiptView
from core.views import (
    admin_dashboard,
    ajax_login,
    ajax_register,
    command_center,
    command_center_create_parcel,
    command_center_create_booking,
    command_center_create_route,
    command_center_create_vehicle,
    command_center_delete_parcel,
    command_center_delete_booking,
    command_center_delete_route,
    command_center_delete_vehicle,
    command_center_edit_parcel,
    command_center_edit_booking,
    command_center_edit_route,
    command_center_edit_vehicle,
    command_center_update_booking_status,
    create_parcel_shipment,
    CustomerLoginView,
    CustomerLogoutView,
    dashboard,
    home,
    register,
    search_results,
    public_track_parcel,
    update_theme_preference,
    update_profile,
    user_dashboard,
)

# Set up the DRF Router for the ViewSets
router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet)
router.register(r'routes', RouteViewSet)

urlpatterns = [
    path('', home, name='home'),
    path('search/', search_results, name='search-results'),
    path('track/', public_track_parcel, name='public-track'),
    path('register/', register, name='register'),
    path('auth/ajax/login/', ajax_login, name='ajax-login'),
    path('auth/ajax/register/', ajax_register, name='ajax-register'),
    path('login/', CustomerLoginView.as_view(), name='login'),
    path('logout/', CustomerLogoutView.as_view(), name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/user/', user_dashboard, name='user-dashboard'),
    path('dashboard/admin/', admin_dashboard, name='admin-dashboard'),
    path('profile/update/', update_profile, name='profile-update'),
    path('profile/theme/', update_theme_preference, name='profile-theme-update'),
    path('parcels/create/', create_parcel_shipment, name='parcel-create'),
    path('command-center/', command_center, name='command-center'),
    path('command-center/bookings/create/', command_center_create_booking, name='command-center-booking-create'),
    path('command-center/bookings/<int:pk>/status/', command_center_update_booking_status, name='command-center-booking-status-update'),
    path('command-center/bookings/<int:pk>/edit/', command_center_edit_booking, name='command-center-booking-edit'),
    path('command-center/bookings/<int:pk>/delete/', command_center_delete_booking, name='command-center-booking-delete'),
    path('command-center/vehicles/create/', command_center_create_vehicle, name='command-center-vehicle-create'),
    path('command-center/vehicles/<int:pk>/edit/', command_center_edit_vehicle, name='command-center-vehicle-edit'),
    path('command-center/vehicles/<int:pk>/delete/', command_center_delete_vehicle, name='command-center-vehicle-delete'),
    path('command-center/routes/create/', command_center_create_route, name='command-center-route-create'),
    path('command-center/routes/<int:pk>/edit/', command_center_edit_route, name='command-center-route-edit'),
    path('command-center/routes/<int:pk>/delete/', command_center_delete_route, name='command-center-route-delete'),
    path('command-center/parcels/create/', command_center_create_parcel, name='command-center-parcel-create'),
    path('command-center/parcels/<int:pk>/edit/', command_center_edit_parcel, name='command-center-parcel-edit'),
    path('command-center/parcels/<int:pk>/delete/', command_center_delete_parcel, name='command-center-parcel-delete'),
    path('bookings/create/', BookingListCreateAPIView.as_view(), name='booking-create'),
    path('bookings/<int:pk>/receipt/', BookingReceiptView.as_view(), name='booking-receipt'),
    path('admin/', admin.site.urls),
    
    # URL for the ViewSets (Vehicles & Routes)
    path('api/', include(router.urls)), 
    
    # URL for the explicit APIView (Bookings)
    path('api/bookings/', BookingListCreateAPIView.as_view(), name='booking-list-create'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static')
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)