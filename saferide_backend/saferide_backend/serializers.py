# saferide_backend/serializers.py
from rest_framework import serializers
from .models import Violation
from django.conf import settings
class ViolationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Violation
        fields = ['violation_type', 'confidence', 'frame_image']
