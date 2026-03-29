from django.apps import AppConfig

class StreamingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "streaming"

    def ready(self):
        from .rtsp_reader import start_rtsp_reader
        start_rtsp_reader()
