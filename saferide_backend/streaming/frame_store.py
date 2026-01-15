import threading

_lock = threading.Lock()

# Raw latest frame (OpenCV BGR numpy array)
LATEST_RAW_FRAME = None

# Latest annotated output (base64 + violations)
LATEST_ANNOTATED = {
    "annotated_image_base64": None,
    "violation_types": []
}

def set_raw_frame(frame):
    global LATEST_RAW_FRAME
    with _lock:
        LATEST_RAW_FRAME = frame

def get_raw_frame():
    with _lock:
        return LATEST_RAW_FRAME

def set_annotated_result(annotated_b64, violations):
    with _lock:
        LATEST_ANNOTATED["annotated_image_base64"] = annotated_b64
        LATEST_ANNOTATED["violation_types"] = violations or []

def get_annotated_result():
    with _lock:
        return dict(LATEST_ANNOTATED)
