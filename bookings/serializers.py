from rest_framework import serializers
from django.contrib.auth.models import User
from django.db.models import Sum
import json
from .models import Booking
from .realtime import broadcast_booking_event

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class BookingSerializer(serializers.ModelSerializer):
    customer_details = UserSerializer(source='customer', read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ('customer', 'seats_booked', 'total_price', 'created_at', 'customer_details')

    def _normalize_seat_numbers(self, raw_seat_numbers):
        seat_numbers = raw_seat_numbers

        if isinstance(seat_numbers, str):
            try:
                seat_numbers = json.loads(seat_numbers)
            except json.JSONDecodeError as exc:
                raise serializers.ValidationError({'seat_numbers': 'Seat numbers must be a valid JSON array.'}) from exc

        if not isinstance(seat_numbers, list) or not seat_numbers:
            raise serializers.ValidationError({'seat_numbers': 'Please select at least one seat.'})

        normalized = []
        for seat in seat_numbers:
            try:
                seat_value = int(seat)
            except (TypeError, ValueError) as exc:
                raise serializers.ValidationError({'seat_numbers': 'Seat numbers must be integers.'}) from exc
            normalized.append(seat_value)

        if len(normalized) != len(set(normalized)):
            raise serializers.ValidationError({'seat_numbers': 'Seat selection contains duplicates.'})

        return normalized

    def validate(self, data):
        vehicle = data.get('vehicle', getattr(self.instance, 'vehicle', None))
        travel_date = data.get('travel_date', getattr(self.instance, 'travel_date', None))
        contact_phone = (data.get('contact_phone', getattr(self.instance, 'contact_phone', '')) or '').strip()
        seat_numbers = self._normalize_seat_numbers(
            data.get('seat_numbers', getattr(self.instance, 'seat_numbers', []))
        )
        seats_requested = len(seat_numbers)

        if not contact_phone:
            raise serializers.ValidationError({'contact_phone': 'Phone number is required for booking communication.'})

        data['contact_phone'] = contact_phone

        if vehicle:
            invalid = [seat for seat in seat_numbers if seat < 1 or seat > vehicle.capacity]
            if invalid:
                raise serializers.ValidationError(
                    {'seat_numbers': f'Seats must be between 1 and {vehicle.capacity}.'}
                )

        data['seat_numbers'] = seat_numbers
        data['seats_booked'] = seats_requested

        if not vehicle or not travel_date:
            return data

        existing_bookings = Booking.objects.filter(
            vehicle=vehicle,
            travel_date=travel_date,
        ).exclude(status='CANCELLED')

        if self.instance and self.instance.pk:
            existing_bookings = existing_bookings.exclude(pk=self.instance.pk)

        booked_seats = []
        for booking in existing_bookings.only('seat_numbers'):
            if isinstance(booking.seat_numbers, list):
                booked_seats.extend(booking.seat_numbers)
        overlap = sorted(set(booked_seats).intersection(seat_numbers))
        if overlap:
            overlap_text = ', '.join(str(seat) for seat in overlap)
            raise serializers.ValidationError({'seat_numbers': f'Seat(s) already booked: {overlap_text}.'})

        total_booked_seats = existing_bookings.aggregate(total=Sum('seats_booked'))['total'] or 0
        available_seats = vehicle.capacity - total_booked_seats

        if seats_requested > available_seats:
            raise serializers.ValidationError({
                'seats_booked': f'Only {available_seats} seat(s) remaining on this vehicle for {travel_date}.'
            })

        return data

    def create(self, validated_data):
        customer = validated_data.pop('customer')
        route = validated_data['route']
        seats_booked = len(validated_data.get('seat_numbers', []))
        validated_data['seats_booked'] = seats_booked
        validated_data['total_price'] = route.base_price * seats_booked
        booking = Booking.objects.create(customer=customer, **validated_data)

        broadcast_booking_event('booking.created', booking)

        return booking