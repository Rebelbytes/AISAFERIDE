import asyncio
import websockets
import base64
import subprocess

RTSP_URL = "rtsp://127.0.0.1:8554/mobile"

ffmpeg = subprocess.Popen(
    [
        "ffmpeg",
        "-loglevel", "warning",
        "-f", "image2pipe",
        "-r", "10",
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        "-pix_fmt", "yuv420p",
        "-rtsp_transport", "tcp",
        "-f", "rtsp",
        RTSP_URL
    ],
    stdin=subprocess.PIPE
)

async def handler(ws):
    async for msg in ws:
        if isinstance(msg, str) and msg.startswith("data:image"):
            jpg = base64.b64decode(msg.split(",")[1])
            ffmpeg.stdin.write(jpg)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 9000):
        print("[VIDEO WS] Listening on ws://0.0.0.0:9000")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
