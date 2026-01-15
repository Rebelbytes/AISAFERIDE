import cv2
import time
import threading
import base64

from .frame_store import set_raw_frame, set_annotated_result

# ✅ Your RTSP stream from MediaMTX
RTSP_URL = "rtsp://127.0.0.1:8554/mobile"

# Limit processing rate so CPU doesn't die
TARGET_FPS = 5


def encode_frame_to_base64_jpeg(frame, quality=70):
    ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        return None
    b64 = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def rtsp_loop():
    cap = cv2.VideoCapture(RTSP_URL)

    if not cap.isOpened():
        print("❌ [RTSP] Could not open RTSP stream:", RTSP_URL)
        return

    print("✅ [RTSP] Connected:", RTSP_URL)

    last_time = 0

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            time.sleep(0.1)
            continue

        # Always update RAW frame (left feed)
        set_raw_frame(frame)

        # Control annotated processing FPS
        now = time.time()
        if now - last_time >= (1 / TARGET_FPS):
            last_time = now

            # ✅ TEMP: no YOLO here yet
            # We'll annotate using your existing YOLO view logic later.
            # For now, just publish same raw frame as "annotated" so UI works.

            annotated_b64 = encode_frame_to_base64_jpeg(frame)
            set_annotated_result(annotated_b64, [])

        time.sleep(0.001)


_started = False

def start_rtsp_reader():
    global _started
    if _started:
        return
    _started = True

    t = threading.Thread(target=rtsp_loop, daemon=True)
    t.start()
    print("🚀 [RTSP] Reader thread started")
