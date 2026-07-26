from rest_framework import serializers
from .models import Vehicle

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        # This tells the API to expose all fields, including the ID and status
        fields = '__all__'