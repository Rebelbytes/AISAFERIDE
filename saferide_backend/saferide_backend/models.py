from django.db import models

class Violation(models.Model):
    frame_image = models.ImageField(upload_to='violation_frames/')
    violation_type = models.CharField(max_length=100)
    confidence = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f"{self.violation_type} - {self.confidence}"