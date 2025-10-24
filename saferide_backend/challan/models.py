from django.db import models
from accounts.models import VehicleOwner


class Challan(models.Model):
    owner = models.ForeignKey(VehicleOwner, on_delete=models.SET_NULL, null=True, blank=True)
    vehicle_number = models.CharField(max_length=15)   # store detected plate (always)
    violation_type = models.CharField(max_length=100)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_issued = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="Pending")
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Challan {self.id} - {self.vehicle_number} - {self.violation_type}"
