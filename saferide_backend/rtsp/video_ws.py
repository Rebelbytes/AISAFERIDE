import asyncio
import websockets
import base64
import subprocess
import time

RTSP_URL = "rtsp://127.0.0.1:8554/mobile"

ffmpeg = None
ACTIVE_CLIENT = None


def start_ffmpeg():
    global ffmpeg
    if ffmpeg is not None and ffmpeg.poll() is None:
        return  # already running

    print("[FFMPEG] Starting ffmpeg ->", RTSP_URL)

    ffmpeg = subprocess.Popen(
        [
            "ffmpeg",
            "-loglevel", "warning",

            # input: jpeg frames from stdin
            "-f", "image2pipe",
            "-r", "10",
            "-i", "-",

            # encode: fast H264
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-pix_fmt", "yuv420p",

            # 🔥 keyframe every 1 second so new viewers instantly lock stream
            "-g", "10",
            "-keyint_min", "10",
            "-sc_threshold", "0",

            # output RTSP
            "-rtsp_transport", "tcp",
            "-f", "rtsp",
            RTSP_URL
        ],
        stdin=subprocess.PIPE
    )


def stop_ffmpeg():
    global ffmpeg
    if ffmpeg is None:
        return

    try:
        ffmpeg.stdin.close()
    except:
        pass

    try:
        ffmpeg.terminate()
    except:
        pass

    ffmpeg = None
    print("[FFMPEG] Stopped")


def write_frame(jpg_bytes: bytes):
    global ffmpeg

    # ensure ffmpeg running
    start_ffmpeg()

    # if ffmpeg died, restart
    if ffmpeg is None or ffmpeg.poll() is not None:
        print("[FFMPEG] ffmpeg not running, restarting...")
        stop_ffmpeg()
        start_ffmpeg()

    try:
        ffmpeg.stdin.write(jpg_bytes)
        ffmpeg.stdin.flush()
    except Exception as e:
        # Broken pipe or invalid argument -> restart ffmpeg
        print("[FFMPEG] Write failed:", repr(e))
        stop_ffmpeg()
        time.sleep(0.2)
        start_ffmpeg()


async def handler(ws):
    global ACTIVE_CLIENT

    # ✅ Single incoming source
    if ACTIVE_CLIENT is not None:
        await ws.close(code=4000, reason="Another device is already streaming")
        return

    ACTIVE_CLIENT = ws
    print("✅ [WS] Client connected:", ws.remote_address)

    try:
        async for msg in ws:
            if isinstance(msg, str) and msg.startswith("data:image"):
                jpg = base64.b64decode(msg.split(",")[1])
                write_frame(jpg)
    except Exception as e:
        print("⚠️ [WS] Client error:", repr(e))
    finally:
        ACTIVE_CLIENT = None
        print("❌ [WS] Client disconnected")
        # optional: stop ffmpeg when client disconnects
        stop_ffmpeg()


async def main():
    print("[VIDEO WS] Listening on ws://0.0.0.0:9000")
    async with websockets.serve(handler, "0.0.0.0", 9000):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
