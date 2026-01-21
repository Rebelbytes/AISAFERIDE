import threading
import time

_lock = threading.Lock()

LATEST_RAW_FRAME = None
LATEST_RAW_TS = 0

LATEST_ANNOTATED = {
    "annotated_image_base64": None,
    "violation_types": []
}
LATEST_ANN_TS = 0

STALE_SECONDS = 3  # if no new frame for 3 seconds -> treat as disconnected


def set_raw_frame(frame):
    global LATEST_RAW_FRAME, LATEST_RAW_TS
    with _lock:
        LATEST_RAW_FRAME = frame
        LATEST_RAW_TS = time.time()


def get_raw_frame():
    with _lock:
        if LATEST_RAW_FRAME is None:
            return None

        if (time.time() - LATEST_RAW_TS) > STALE_SECONDS:
            return None

        return LATEST_RAW_FRAME


def set_annotated_result(annotated_b64, violations):
    global LATEST_ANNOTATED, LATEST_ANN_TS
    with _lock:
        LATEST_ANNOTATED["annotated_image_base64"] = annotated_b64
        LATEST_ANNOTATED["violation_types"] = violations or []
        LATEST_ANN_TS = time.time()


def get_annotated_result():
    with _lock:
        if not LATEST_ANNOTATED["annotated_image_base64"]:
            return dict(LATEST_ANNOTATED)

        if (time.time() - LATEST_ANN_TS) > STALE_SECONDS:
            return {
                "annotated_image_base64": None,
                "violation_types": []
            }

        return dict(LATEST_ANNOTATED)
