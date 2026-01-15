from django.urls import path
from .views import raw_frame_view, annotated_view

urlpatterns = [
    path("raw/", raw_frame_view),
    path("annotated/", annotated_view),
]
