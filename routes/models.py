from django.db import models

class Route(models.Model):
    origin = models.CharField(max_length=150)
    destination = models.CharField(max_length=150)
    distance_km = models.DecimalField(max_digits=6, decimal_places=2)
    base_price = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.origin} to {self.destination}"