import os
import uuid
import time
import math
import cv2
from datetime import datetime
from django.conf import settings
from saferide_backend.models import Violation
from saferide_backend.license_plate_ocr import LicensePlateOCR

from .yolo_service import detect_frame  # we'll create this file too


# lp_ocr = LicensePlateOCR()

# ✅ prevent spam duplicates (same violation repeatedly)
LAST_SAVED = {}  # key -> timestamp
SAVE_COOLDOWN_SECONDS = 4


def should_save_violation(vtype):
    now = time.time()
    last = LAST_SAVED.get(vtype, 0)
    if now - last < SAVE_COOLDOWN_SECONDS:
        return False
    LAST_SAVED[vtype] = now
    return True


def save_live_violation(frame, violation, plates):
    """
    Saves a live violation without OCR.

    Args:
        frame (np.ndarray): Annotated frame with drawn boxes.
        violation (dict): {
            "type": str,
            "confidence": float,
            "bbox": (x1, y1, x2, y2)
        }
        plates (list): List of detected number plate bounding boxes.

    Returns:
        Violation | None
    """
    vtype = violation["type"]
    conf = violation["confidence"]
    x1, y1, x2, y2 = violation["bbox"]

    # Prevent duplicate spam
    if not should_save_violation(vtype):
        return None

    # Save annotated frame
    frame_name = f"live_frame_{uuid.uuid4()}.jpg"
    frame_dir = os.path.join(settings.MEDIA_ROOT, "violations")
    os.makedirs(frame_dir, exist_ok=True)
    frame_path = os.path.join(frame_dir, frame_name)
    cv2.imwrite(frame_path, frame)

    # Save nearest plate image (NO OCR)
    plate_path_rel = None

    if plates:
        vx, vy = (x1 + x2) // 2, (y1 + y2) // 2
        nearest_plate = min(
            plates,
            key=lambda p: math.hypot(
                vx - (p[0] + p[2]) // 2,
                vy - (p[1] + p[3]) // 2
            )
        )

        px1, py1, px2, py2 = nearest_plate
        plate_crop = frame[py1:py2, px1:px2]

        if plate_crop.size > 0:
            plate_name = f"live_plate_{uuid.uuid4()}.jpg"
            plate_dir = os.path.join(settings.MEDIA_ROOT, "license_plates")
            os.makedirs(plate_dir, exist_ok=True)
            abs_plate_path = os.path.join(plate_dir, plate_name)

            cv2.imwrite(abs_plate_path, plate_crop)
            plate_path_rel = os.path.join("license_plates", plate_name)

    return Violation.objects.create(
        frame_image=os.path.join("violations", frame_name),
        license_plate_image=plate_path_rel,
        violation_type=vtype,
        confidence=conf
    )

def run_live_pipeline(raw_frame):
    """
    Runs the YOLO + saving pipeline on an incoming RTSP frame.

    Args:
        raw_frame (np.ndarray): Original BGR image frame from OpenCV.

    Returns:
        tuple[np.ndarray, list]:
            annotated_frame: Frame with drawn boxes/labels.
            violations_found: List of detected violations for UI and saving.
    """
    try:
        # ✅ Use a copy so raw feed is never modified
        annotated_frame, violations_found, plates_found = detect_frame(raw_frame.copy())

        # ✅ Save violations like uploaded video loop
        for violation in violations_found:
            save_live_violation(annotated_frame, violation, plates_found)

        return annotated_frame, violations_found

    except Exception as e:
        # ✅ If YOLO/OCR crashes for any reason, keep stream alive
        print("❌ [LIVE PIPELINE ERROR]", str(e))

        # Fallback: return original raw frame with no violations
        return raw_frame, []

