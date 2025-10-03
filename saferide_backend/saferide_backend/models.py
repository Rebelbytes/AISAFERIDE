# models.py
from django.db import models

class Violation(models.Model):
    frame_image = models.ImageField(upload_to="violation_frames")
    violation_type = models.CharField(max_length=50)
    confidence = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Violation {self.id} - {self.violation_type}"
