from django.urls import path
from .views import GenerateChallanView, ChallanListView, ChallanDetailView

urlpatterns = [
    path('generate/', GenerateChallanView.as_view(), name='generate_challan'),
    path('list/', ChallanListView.as_view(), name='challan_list'),
    path('<int:challan_id>/', ChallanDetailView.as_view(), name='challan_detail'),
]
