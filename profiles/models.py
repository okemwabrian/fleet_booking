from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    THEME_CHOICES = [
        ('system', 'System'),
        ('light', 'Light'),
        ('dark', 'Dark'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone_number = models.CharField(max_length=30, blank=True)
    preferences = models.JSONField(default=dict, blank=True)
    theme_preference = models.CharField(max_length=10, choices=THEME_CHOICES, default='system')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profile for {self.user.username}'
