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
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking #{self.id} - {self.customer.username} on {self.travel_date}"