"""
URL configuration for saferide_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from .views import home, DetectView, LiveDetectView, SaveViolationView, SavedViolationsView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),
    path("api/", include("accounts.urls")),  # ✅ now it will find accounts/urls.py
    path("api/detect/", DetectView.as_view(), name="detect"),
    path("api/live-detect/", LiveDetectView.as_view(), name="live_detect"),
    path("api/save-violation/", SaveViolationView.as_view(), name="save_violation"),
    path("api/saved-violations/", SavedViolationsView.as_view(), name="saved_violations"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
