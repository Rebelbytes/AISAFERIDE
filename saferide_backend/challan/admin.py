from django.contrib import admin
from .models import Challan
from accounts.models import VehicleOwner


@admin.register(Challan)
class ChallanAdmin(admin.ModelAdmin):
	list_display = ("id", "vehicle_number", "violation_type", "fine_amount", "status", "date_issued")
	search_fields = ("vehicle_number", "violation_type", "owner__owner_name")
	list_filter = ("status", "date_issued")

	class Meta:
		model = Challan


@admin.register(VehicleOwner)
class VehicleOwnerAdmin(admin.ModelAdmin):
	list_display = ("owner_name", "vehicle_number", "email", "phone")
	search_fields = ("owner_name", "vehicle_number", "email")
	list_filter = ("created_at",)

	class Meta:
		model = VehicleOwner
                                                                                                