from django.contrib.auth.models import AbstractUser
from django.db import models

class Officer(AbstractUser):
    officer_id = models.CharField(max_length=50, unique=True)
    officer_name = models.CharField(max_length=100)
    batch = models.CharField(max_length=50, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(unique=True)  # 👈 make email unique

    USERNAME_FIELD = "email"   # 👈 now login with email
    REQUIRED_FIELDS = ["officer_id", "officer_name"]  

    def __str__(self):
        return f"{self.officer_name} ({self.officer_id})"


class VehicleOwner(models.Model):
    owner_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    vehicle_number = models.CharField(max_length=15, unique=True)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.owner_name} - {self.vehicle_number}"