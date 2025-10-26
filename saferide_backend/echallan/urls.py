from django.urls import path
from .views import (
    EChallanListView,
    EChallanDetailView,
    SendEmailView,
    DownloadPDFView,
    EChallanStatsView
)

urlpatterns = [
    path('', EChallanListView.as_view(), name='echallan_list'),
    path('stats/', EChallanStatsView.as_view(), name='echallan_stats'),
    path('<int:echallan_id>/', EChallanDetailView.as_view(), name='echallan_detail'),
    path('<int:echallan_id>/send-email/', SendEmailView.as_view(), name='send_email'),
    path('<int:echallan_id>/download-pdf/', DownloadPDFView.as_view(), name='download_pdf'),
]
