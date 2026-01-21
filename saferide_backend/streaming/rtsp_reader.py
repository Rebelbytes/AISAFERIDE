import cv2
import time
import threading
import base64

from .frame_store import set_raw_frame, set_annotated_result
from saferide_backend.live_pipeline import run_live_pipeline


# ✅ Your RTSP stream from MediaMTX
RTSP_URL = "rtsp://127.0.0.1:8554/mobile"

# Limiting the processing rate so CPU doesn't die
TARGET_FPS = 2  # 2-3 FPS for demo


def encode_frame_to_base64_jpeg(frame, quality=70):
    ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        return None
    b64 = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def rtsp_loop():
    print("🚀 [RTSP] Reader loop started (auto-reconnect enabled)")
    
    while True:
        cap = None
        try:
            print("🔌 [RTSP] Connecting:", RTSP_URL)
            cap = cv2.VideoCapture(RTSP_URL)

            if not cap.isOpened():
                print("❌ [RTSP] Could not open RTSP stream:", RTSP_URL)
                time.sleep(2)
                continue

            print("✅ [RTSP] Connected:", RTSP_URL)

            last_time = 0
            last_ok_time = time.time()

            while True:
                ret, frame = cap.read()

                if not ret or frame is None:
                    # if no frames for 3 seconds -> reconnect
                    if time.time() - last_ok_time > 3.0:
                        print("⚠️ [RTSP] No frames for 3s -> reconnecting...")
                        break

                    time.sleep(0.05)
                    continue

                last_ok_time = time.time()

                # Always update RAW frame (left feed)
                set_raw_frame(frame)

                # Control annotated processing FPS
                now = time.time()
                if now - last_time >= (1 / TARGET_FPS):
                    last_time = now

                    # ✅ Run live YOLO + auto save violations
                    annotated_frame, violations = run_live_pipeline(frame)
                    annotated_b64 = encode_frame_to_base64_jpeg(annotated_frame)

                    # store for frontend polling
                    set_annotated_result(annotated_b64, violations)

                time.sleep(0.001)

        except Exception as e:
            print("❌ [RTSP] Reader crashed:", str(e))

        finally:
            try:
                if cap is not None:
                    cap.release()
            except:
                pass

        # reconnect delay
        time.sleep(1)

_started = False

def start_rtsp_reader():
    global _started
    if _started:
        return
    _started = True

    t = threading.Thread(target=rtsp_loop, daemon=True)
    t.start()
    print("🚀 [RTSP] Reader thread started")
