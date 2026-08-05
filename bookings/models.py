from django.db import models
from django.contrib.auth.models import User
from vehicles.models import Vehicle
from routes.models import Route

class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, related_name='bookings')
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, related_name='bookings')
    
    travel_date = models.DateField()
    seat_numbers = models.JSONField(default=list)
    seats_booked = models.PositiveIntegerField(default=1)
    payment_proof = models.ImageField(upload_to='payment_proofs/', blank=True, null=True)
    contact_phone = models.CharField(max_length=30, blank=True, default='')
    contact_email = models.EmailField(blank=True, default='')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking #{self.id} - {self.customer.username} ({self.seats_booked} seats) on {self.travel_date}"


class ParcelShipment(models.Model):
    STATUS_RECEIVED = 'RECEIVED'
    STATUS_IN_TRANSIT = 'IN_TRANSIT'
    STATUS_ARRIVED = 'ARRIVED'
    STATUS_DELIVERED = 'DELIVERED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_RECEIVED, 'Received'),
        (STATUS_IN_TRANSIT, 'In transit'),
        (STATUS_ARRIVED, 'Arrived at destination hub'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='parcels')
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True, related_name='parcels')
    tracking_code = models.CharField(max_length=20, unique=True)

    sender_name = models.CharField(max_length=150)
    sender_phone = models.CharField(max_length=30)
    sender_email = models.EmailField(blank=True)

    receiver_name = models.CharField(max_length=150)
    receiver_phone = models.CharField(max_length=30)
    receiver_email = models.EmailField(blank=True)

    parcel_description = models.CharField(max_length=255)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_RECEIVED)
    current_location = models.CharField(max_length=150, blank=True)
    expected_delivery_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Parcel {self.tracking_code} ({self.get_status_display()})"