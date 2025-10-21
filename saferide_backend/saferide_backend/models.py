# models.py
from django.db import models

class Violation(models.Model):
    frame_image = models.ImageField(upload_to="violation_frames")
    license_plate_image = models.ImageField(upload_to="license_plates", null=True, blank=True)
    violation_type = models.CharField(max_length=50)
    confidence = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    # New fields for OCR results
    license_plate_text = models.CharField(max_length=20, null=True, blank=True)
    ocr_confidence = models.FloatField(default=0.0)
    ocr_method = models.CharField(max_length=50, default='Unknown')
    

    def __str__(self):
        return f"Violation {self.id} - {self.violation_type}"
