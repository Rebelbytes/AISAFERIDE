from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from .models import EChallan
from accounts.models import VehicleOwner
from .serializers import EChallanSerializer, EChallanCreateSerializer
import json
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


class EChallanListView(APIView):
    def get(self, request):
        """
        Get all eChallans with optional filtering
        """
        queryset = EChallan.objects.all()
        
        # Search by vehicle number
        vehicle_number = request.query_params.get('vehicle_number', None)
        if vehicle_number:
            queryset = queryset.filter(vehicle_number__icontains=vehicle_number)
        
        # Filter by status
        status_filter = request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by violation type
        violation_type = request.query_params.get('violation_type', None)
        if violation_type:
            queryset = queryset.filter(violation_type__icontains=violation_type)
        
        # Filter by date range
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(date_issued__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_issued__date__lte=end_date)
        
        # Order by most recent first
        queryset = queryset.order_by('-date_issued')
        
        serializer = EChallanSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """
        Create a new eChallan
        """
        try:
            vehicle_number = request.data.get('vehicle_number')
            violation_type = request.data.get('violation_type')
            fine_amount = request.data.get('fine_amount')
            
            if not vehicle_number or not violation_type or not fine_amount:
                return Response({
                    'error': 'Vehicle number, violation type, and fine amount are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Try to find the vehicle owner
            try:
                vehicle_owner = VehicleOwner.objects.get(vehicle_number=vehicle_number)
            except VehicleOwner.DoesNotExist:
                vehicle_owner = None
            
            # Create the eChallan
            echallan = EChallan.objects.create(
                owner=vehicle_owner,
                vehicle_number=vehicle_number,
                violation_type=violation_type,
                fine_amount=fine_amount,
                notes=request.data.get('notes', ''),
                evidence_image=request.data.get('evidence_image'),
                evidence_video=request.data.get('evidence_video'),
                created_by=request.data.get('created_by', 'System')
            )
            
            serializer = EChallanSerializer(echallan)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EChallanDetailView(APIView):
    def get(self, request, echallan_id):
        """
        Get a specific eChallan by ID
        """
        echallan = get_object_or_404(EChallan, id=echallan_id)
        serializer = EChallanSerializer(echallan)
        return Response(serializer.data)
    
    def patch(self, request, echallan_id):
        """
        Update eChallan status and other fields
        """
        echallan = get_object_or_404(EChallan, id=echallan_id)
        
        # Update status
        if 'status' in request.data:
            echallan.status = request.data['status']
            
            # Set payment date if status is changed to Paid
            if request.data['status'] == 'Paid':
                from django.utils import timezone
                echallan.payment_date = timezone.now()
            
            # Set dispute date if status is changed to Disputed
            if request.data['status'] == 'Disputed':
                from django.utils import timezone
                echallan.dispute_date = timezone.now()
                echallan.dispute_reason = request.data.get('dispute_reason', '')
        
        # Update other fields
        if 'notes' in request.data:
            echallan.notes = request.data['notes']
        if 'dispute_reason' in request.data:
            echallan.dispute_reason = request.data['dispute_reason']
        
        echallan.save()
        
        serializer = EChallanSerializer(echallan)
        return Response(serializer.data)
    
    def delete(self, request, echallan_id):
        """
        Delete an eChallan (admin only)
        """
        echallan = get_object_or_404(EChallan, id=echallan_id)
        echallan.delete()
        return Response({'message': 'EChallan deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


class SendEmailView(APIView):
    def post(self, request, echallan_id):
        """
        Send email notification for eChallan
        """
        echallan = get_object_or_404(EChallan, id=echallan_id)
        
        if not echallan.owner or not echallan.owner.email:
            return Response({
                'error': 'No email address found for this eChallan'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            subject = f'Traffic Violation EChallan #{echallan.id}'
            message = f"""
Dear {echallan.owner.owner_name},

You have been issued a traffic violation eChallan with the following details:

EChallan ID: {echallan.id}
Vehicle Number: {echallan.vehicle_number}
Violation Type: {echallan.violation_type}
Fine Amount: ₹{echallan.fine_amount}
Issue Date: {echallan.date_issued.strftime('%Y-%m-%d %H:%M')}
Status: {echallan.status}

Please pay the fine amount within the specified time to avoid additional penalties.

Thank you,
SafeRide Traffic Management System
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [echallan.owner.email],
                fail_silently=False,
            )
            
            return Response({
                'message': 'Email sent successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to send email: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DownloadPDFView(APIView):
    def get(self, request, echallan_id):
        """
        Generate and download PDF for eChallan
        """
        echallan = get_object_or_404(EChallan, id=echallan_id)
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Define custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Build PDF content
        story = []
        
        # Title
        story.append(Paragraph("TRAFFIC VIOLATION ECHALLAN", title_style))
        story.append(Spacer(1, 20))
        
        # EChallan details table
        echallan_data = [
            ['EChallan ID:', str(echallan.id)],
            ['Vehicle Number:', echallan.vehicle_number],
            ['Owner Name:', echallan.owner.owner_name if echallan.owner else 'N/A'],
            ['Email:', echallan.owner.email if echallan.owner else 'N/A'],
            ['Phone:', echallan.owner.phone if echallan.owner else 'N/A'],
            ['Violation Type:', echallan.violation_type],
            ['Fine Amount:', f'₹{echallan.fine_amount}'],
            ['Issue Date:', echallan.date_issued.strftime('%Y-%m-%d %H:%M')],
            ['Status:', echallan.status],
        ]
        
        if echallan.notes:
            echallan_data.append(['Notes:', echallan.notes])
        
        if echallan.dispute_reason:
            echallan_data.append(['Dispute Reason:', echallan.dispute_reason])
        
        table = Table(echallan_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # Footer note
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        story.append(Paragraph("This is an automated eChallan generated by SafeRide Traffic Management System", footer_style))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF content
        buffer.seek(0)
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Create HTTP response
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="echallan_{echallan.id}.pdf"'
        
        return response


class EChallanStatsView(APIView):
    def get(self, request):
        """
        Get statistics for eChallans
        """
        total_echallans = EChallan.objects.count()
        pending_echallans = EChallan.objects.filter(status='Pending').count()
        paid_echallans = EChallan.objects.filter(status='Paid').count()
        disputed_echallans = EChallan.objects.filter(status='Disputed').count()
        cancelled_echallans = EChallan.objects.filter(status='Cancelled').count()
        
        # Violation type breakdown
        violation_stats = {}
        for echallan in EChallan.objects.all():
            violation_type = echallan.violation_type
            if violation_type in violation_stats:
                violation_stats[violation_type] += 1
            else:
                violation_stats[violation_type] = 1
        
        # Total fine amount
        total_fine_amount = sum(echallan.fine_amount for echallan in EChallan.objects.all())
        
        return Response({
            'total_echallans': total_echallans,
            'pending_echallans': pending_echallans,
            'paid_echallans': paid_echallans,
            'disputed_echallans': disputed_echallans,
            'cancelled_echallans': cancelled_echallans,
            'violation_stats': violation_stats,
            'total_fine_amount': float(total_fine_amount)
        })
