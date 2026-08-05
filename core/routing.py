from django.urls import path

from bookings.consumers import BookingDispatcherConsumer
from messaging.consumers import DirectMessageConsumer

websocket_urlpatterns = [
    path('ws/bookings/', BookingDispatcherConsumer.as_asgi()),
    path('ws/messages/', DirectMessageConsumer.as_asgi()),
]