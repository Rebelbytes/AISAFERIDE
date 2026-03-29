from django.urls import path
from .views import RawFrameView, AnnotatedFrameView

urlpatterns = [
    path("raw/", RawFrameView.as_view(), name="stream_raw"),
    path("annotated/", AnnotatedFrameView.as_view(), name="stream_annotated"),
]
