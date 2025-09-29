from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.OfficerRegisterView.as_view(), name="officer-register"),
    path("login/", views.OfficerLoginView.as_view(), name="officer-login"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
]
