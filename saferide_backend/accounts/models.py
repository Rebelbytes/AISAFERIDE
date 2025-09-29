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
