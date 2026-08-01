from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import your Views
from vehicles.views import VehicleViewSet
from routes.views import RouteViewSet
from bookings.views import BookingListCreateAPIView

# Set up the DRF Router for the ViewSets
router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet)
router.register(r'routes', RouteViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # URL for the ViewSets (Vehicles & Routes)
    path('api/', include(router.urls)), 
    
    # URL for the explicit APIView (Bookings)
    path('api/bookings/', BookingListCreateAPIView.as_view(), name='booking-list-create'),
]