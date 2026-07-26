from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Booking

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class BookingSerializer(serializers.ModelSerializer):
    # This embeds the user's readable details instead of just showing their ID number
    customer_details = UserSerializer(source='customer', read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'