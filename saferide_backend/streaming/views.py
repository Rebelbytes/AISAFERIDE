import cv2
import base64

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .frame_store import get_raw_frame, get_annotated_result


class RawFrameView(APIView):
    """
    Returns latest RAW frame from RTSP reader
    Used for LEFT side feed (raw)
    GET: /stream/raw/
    """
    def get(self, request):
        frame = get_raw_frame()

        if frame is None:
            return Response(
                {"status": "waiting", "message": "No raw frame yet"},
                status=status.HTTP_200_OK
            )

        ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if not ok:
            return Response(
                {"status": "error", "message": "Encoding failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        b64 = base64.b64encode(buffer).decode("utf-8")

        return Response(
            {
                "status": "ok",
                "image_base64": f"data:image/jpeg;base64,{b64}"
            },
            status=status.HTTP_200_OK
        )


class AnnotatedFrameView(APIView):
    """
    Returns latest ANNOTATED frame + violation list
    Used for RIGHT side feed (annotated + detected)
    GET: /stream/annotated/
    """
    def get(self, request):
        data = get_annotated_result()

        if not data.get("annotated_image_base64"):
            return Response(
                {"status": "waiting", "message": "No annotated frame yet"},
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "status": "ok",
                "annotated_image_base64": data["annotated_image_base64"],
                "violation_types": data.get("violation_types", [])
            },
            status=status.HTTP_200_OK
        )
