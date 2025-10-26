from django.db import models
from accounts.models import VehicleOwner


class EChallan(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Disputed', 'Disputed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    VIOLATION_CHOICES = [
        ('No Helmet', 'No Helmet'),
        ('Triple Riding', 'Triple Riding'),
        ('Right Side', 'Right Side'),
        ('Wrong Side', 'Wrong Side'),
        ('Using Mobile', 'Using Mobile'),
        ('Vehicle No License Plate', 'Vehicle No License Plate'),
        ('Red Light Jumping', 'Red Light Jumping'),
        ('Overspeeding', 'Overspeeding'),
        ('No Seat Belt', 'No Seat Belt'),
    ]
    
    owner = models.ForeignKey(VehicleOwner, on_delete=models.SET_NULL, null=True, blank=True)
    vehicle_number = models.CharField(max_length=15)
    violation_type = models.CharField(max_length=100, choices=VIOLATION_CHOICES)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_issued = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    notes = models.TextField(blank=True, null=True)
    evidence_image = models.ImageField(upload_to='echallan_evidence/', blank=True, null=True)
    evidence_video = models.FileField(upload_to='echallan_evidence/', blank=True, null=True)
    dispute_reason = models.TextField(blank=True, null=True)
    dispute_date = models.DateTimeField(blank=True, null=True)
    payment_date = models.DateTimeField(blank=True, null=True)
    created_by = models.CharField(max_length=100, default='System')
    
    def __str__(self):
        return f"EChallan {self.id} - {self.vehicle_number} - {self.violation_type}"
    
    class Meta:
        ordering = ['-date_issued']
        verbose_name = 'EChallan'
        verbose_name_plural = 'EChallans'
