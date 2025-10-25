from rest_framework import serializers
from .models import Challan
from accounts.models import VehicleOwner


class VehicleOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleOwner
        fields = ['id', 'owner_name', 'email', 'phone', 'vehicle_number', 'address', 'created_at']


class ChallanSerializer(serializers.ModelSerializer):
    owner = VehicleOwnerSerializer(read_only=True)
    
    class Meta:
        model = Challan
        fields = ['id', 'owner', 'vehicle_number', 'violation_type', 'fine_amount', 'date_issued', 'status', 'notes']
