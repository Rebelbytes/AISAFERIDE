import cv2
import base64
from django.http import JsonResponse

from .frame_store import get_raw_frame, get_annotated_result


def raw_frame_view(request):
    frame = get_raw_frame()
    if frame is None:
        return JsonResponse({"status": "waiting", "message": "No frame yet"})

    ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    if not ok:
        return JsonResponse({"status": "error", "message": "Encoding failed"}, status=500)

    b64 = base64.b64encode(buffer).decode("utf-8")
    return JsonResponse({
        "status": "ok",
        "image_base64": f"data:image/jpeg;base64,{b64}"
    })


def annotated_view(request):
    data = get_annotated_result()
    if not data["annotated_image_base64"]:
        return JsonResponse({"status": "waiting", "message": "No annotated frame yet"})

    return JsonResponse({
        "status": "ok",
        "annotated_image_base64": data["annotated_image_base64"],
        "violation_types": data["violation_types"]
    })
