from django.contrib import admin
from .models import EChallan


@admin.register(EChallan)
class EChallanAdmin(admin.ModelAdmin):
    list_display = ("id", "vehicle_number", "violation_type", "fine_amount", "status", "date_issued", "created_by")
    search_fields = ("vehicle_number", "violation_type", "owner__owner_name")
    list_filter = ("status", "violation_type", "date_issued", "created_by")
    readonly_fields = ("date_issued", "dispute_date", "payment_date")
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('owner', 'vehicle_number', 'violation_type', 'fine_amount', 'status')
        }),
        ('Details', {
            'fields': ('notes', 'evidence_image', 'evidence_video')
        }),
        ('Dispute Information', {
            'fields': ('dispute_reason', 'dispute_date'),
            'classes': ('collapse',)
        }),
        ('Payment Information', {
            'fields': ('payment_date',),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_by', 'date_issued'),
            'classes': ('collapse',)
        }),
    )
    
    class Meta:
        model = EChallan
