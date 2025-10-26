from rest_framework import serializers
from .models import EChallan
from accounts.models import VehicleOwner


class VehicleOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleOwner
        fields = ['id', 'owner_name', 'email', 'phone', 'vehicle_number', 'address', 'created_at']


class EChallanSerializer(serializers.ModelSerializer):
    owner = VehicleOwnerSerializer(read_only=True)
    
    class Meta:
        model = EChallan
        fields = [
            'id', 'owner', 'vehicle_number', 'violation_type', 'fine_amount', 
            'date_issued', 'status', 'notes', 'evidence_image', 'evidence_video',
            'dispute_reason', 'dispute_date', 'payment_date', 'created_by'
        ]
        read_only_fields = ['id', 'date_issued', 'dispute_date', 'payment_date']


class EChallanCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EChallan
        fields = [
            'vehicle_number', 'violation_type', 'fine_amount', 'notes',
            'evidence_image', 'evidence_video', 'created_by'
        ]
