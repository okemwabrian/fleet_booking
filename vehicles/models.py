from django.db import models

class Vehicle(models.Model):
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('MAINTENANCE', 'In Maintenance'),
        ('UNAVAILABLE', 'Unavailable'),
    ]

    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    license_plate = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.make} {self.model} - {self.license_plate}"