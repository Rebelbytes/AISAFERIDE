from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
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
            
            # Send email notification if vehicle owner exists and has email
            email_sent = False
            email_error = None
            
            if vehicle_owner and vehicle_owner.email:
                try:
                    # Create email content
                    subject = f'Traffic Violation Challan #{challan.id} - {violation_type}'
                    
                    # HTML email template
                    html_message = f"""
                    <html>
                    <head>
                        <style>
                            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                            .header {{ background-color: #dc2626; color: white; padding: 20px; text-align: center; }}
                            .content {{ padding: 20px; background-color: #f9fafb; }}
                            .challan-details {{ background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                            .violation {{ background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 15px 0; }}
                            .fine {{ background-color: #f0fdf4; border-left: 4px solid #16a34a; padding: 15px; margin: 15px 0; }}
                            .footer {{ background-color: #374151; color: white; padding: 15px; text-align: center; font-size: 14px; }}
                            .button {{ background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 10px 0; }}
                        </style>
                    </head>
                    <body>
                        <div class="header">
                            <h1>🚨 Traffic Violation Challan</h1>
                            <p>SafeRide Traffic Management System</p>
                        </div>
                        
                        <div class="content">
                            <h2>Dear {vehicle_owner.owner_name},</h2>
                            
                            <p>You have been issued a traffic violation challan for the following violation:</p>
                            
                            <div class="challan-details">
                                <h3>Challan Details:</h3>
                                <p><strong>Challan ID:</strong> #{challan.id}</p>
                                <p><strong>Vehicle Number:</strong> {challan.vehicle_number}</p>
                                <p><strong>Date & Time:</strong> {challan.date_issued.strftime('%B %d, %Y at %I:%M %p')}</p>
                            </div>
                            
                            <div class="violation">
                                <h3>⚠️ Violation Details:</h3>
                                <p><strong>Violation Type:</strong> {challan.violation_type}</p>
                                <p><strong>Status:</strong> {challan.status}</p>
                            </div>
                            
                            <div class="fine">
                                <h3>💰 Fine Amount:</h3>
                                <p style="font-size: 24px; font-weight: bold; color: #16a34a;">₹{challan.fine_amount}</p>
                            </div>
                            
                            <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 15px 0;">
                                <h3>📋 Important Instructions:</h3>
                                <ul>
                                    <li>Please pay the fine amount within 30 days to avoid additional penalties</li>
                                    <li>You can pay online through the official traffic department website</li>
                                    <li>Keep this challan number for your records: <strong>#{challan.id}</strong></li>
                                    <li>If you believe this challan was issued in error, you can dispute it within 7 days</li>
                                </ul>
                            </div>
                            
                            <p>Thank you for your cooperation in maintaining road safety.</p>
                            
                            <p><strong>SafeRide Traffic Management System</strong><br>
                            Automated Traffic Violation Detection & Management</p>
                        </div>
                        
                        <div class="footer">
                            <p>This is an automated challan generated by SafeRide Traffic Management System</p>
                            <p>For queries, contact: support@saferide.com</p>
                        </div>
                    </body>
                    </html>
                    """
                    
                    # Plain text version
                    plain_message = f"""
Dear {vehicle_owner.owner_name},

You have been issued a traffic violation challan for the following violation:

CHALLAN DETAILS:
- Challan ID: #{challan.id}
- Vehicle Number: {challan.vehicle_number}
- Date & Time: {challan.date_issued.strftime('%B %d, %Y at %I:%M %p')}

VIOLATION DETAILS:
- Violation Type: {challan.violation_type}
- Status: {challan.status}

FINE AMOUNT: ₹{challan.fine_amount}

IMPORTANT INSTRUCTIONS:
- Please pay the fine amount within 30 days to avoid additional penalties
- You can pay online through the official traffic department website
- Keep this challan number for your records: #{challan.id}
- If you believe this challan was issued in error, you can dispute it within 7 days

Thank you for your cooperation in maintaining road safety.

SafeRide Traffic Management System
Automated Traffic Violation Detection & Management

This is an automated challan generated by SafeRide Traffic Management System
For queries, contact: support@saferide.com
                    """
                    
                    # Send email
                    send_mail(
                        subject=subject,
                        message=plain_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[vehicle_owner.email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    
                    email_sent = True
                    
                except Exception as e:
                    email_sent = False
                    email_error = str(e)
                    print(f"Email sending failed: {e}")
            
            # Serialize the response
            challan_data = ChallanSerializer(challan).data
            owner_data = VehicleOwnerSerializer(vehicle_owner).data if vehicle_owner else None
            
            response_data = {
                'challan': challan_data,
                'vehicle_owner': owner_data,
                'message': 'Challan generated successfully',
                'email_sent': email_sent
            }
            
            if email_sent:
                response_data['email_message'] = f'Email notification sent to {vehicle_owner.email}'
            elif vehicle_owner and not vehicle_owner.email:
                response_data['email_message'] = 'No email address found for vehicle owner'
            elif not vehicle_owner:
                response_data['email_message'] = 'Vehicle owner not found in database'
            elif email_error:
                response_data['email_message'] = f'Email sending failed: {email_error}'
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
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
