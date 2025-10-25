from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Challan
from accounts.models import VehicleOwner
from .serializers import ChallanSerializer, VehicleOwnerSerializer
import json


class GenerateChallanView(APIView):
    def post(self, request):
        """
        Generate a challan for a vehicle number and violation type
        """
        try:
            vehicle_number = request.data.get('vehicle_number')
            violation_type = request.data.get('violation_type')
            
            if not vehicle_number or not violation_type:
                return Response({
                    'error': 'Vehicle number and violation type are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Try to find the vehicle owner
            try:
                vehicle_owner = VehicleOwner.objects.get(vehicle_number=vehicle_number)
            except VehicleOwner.DoesNotExist:
                vehicle_owner = None
            
            # Define fine amounts based on violation type
            fine_amounts = {
                'No Helmet': 1000.00,
                'Triple Riding': 2000.00,
                'Right Side': 500.00,
                'Wrong Side': 1000.00,
                'Using Mobile': 1500.00,
                'Vehicle No License Plate': 2000.00,
            }
            
            fine_amount = fine_amounts.get(violation_type, 1000.00)
            
            # Create the challan
            challan = Challan.objects.create(
                owner=vehicle_owner,
                vehicle_number=vehicle_number,
                violation_type=violation_type,
                fine_amount=fine_amount,
                status='Pending'
            )
            
            # Serialize the response
            challan_data = ChallanSerializer(challan).data
            owner_data = VehicleOwnerSerializer(vehicle_owner).data if vehicle_owner else None
            
            return Response({
                'challan': challan_data,
                'vehicle_owner': owner_data,
                'message': 'Challan generated successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChallanListView(APIView):
    def get(self, request):
        """
        Get all challans
        """
        challans = Challan.objects.all().order_by('-date_issued')
        serializer = ChallanSerializer(challans, many=True)
        return Response(serializer.data)


class ChallanDetailView(APIView):
    def get(self, request, challan_id):
        """
        Get a specific challan by ID
        """
        challan = get_object_or_404(Challan, id=challan_id)
        serializer = ChallanSerializer(challan)
        return Response(serializer.data)
    
    def patch(self, request, challan_id):
        """
        Update challan status
        """
        challan = get_object_or_404(Challan, id=challan_id)
        challan.status = request.data.get('status', challan.status)
        challan.notes = request.data.get('notes', challan.notes)
        challan.save()
        
        serializer = ChallanSerializer(challan)
        return Response(serializer.data)
