from rest_framework import serializers
from .models import Officer

class OfficerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Officer
        fields = ['id', 'officer_id', 'badge_number', 'station', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        officer = Officer.objects.create_user(**validated_data)
        return officer
