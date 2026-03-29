
# Saferide AI Project 🚦
# Traffic Violation Detection System using Real-Time AI Analytics

This project consists of:
- **Backend:** Django + DRF for AI violation detection, storage, and APIs.
- **Frontend:** React for UI dashboard + live monitoring.
- **Live Streaming Prototype:**
  - **Mobile Browser:** Acts as the camera sender.
  - **WebSocket Server:** Receives frames from mobile (`video_ws.py`).
  - **FFmpeg:** Converts frames → RTSP stream.
  - **MediaMTX:** Hosts the RTSP path (`rtsp://127.0.0.1:8554/mobile`).
  - **Django:** Reads RTSP stream and serves Raw and Annotated (YOLO) feeds.

---

## 🛠️ Prerequisites

### Backend Requirements
- Python 3.8+
- pip
- Git
- Libraries: opencv-python, ultralytics, django, djangorestframework

### Frontend Requirements
- Node.js 16+
- npm or yarn

### Live Streaming Requirements
- MediaMTX (RTSP Server)
- FFmpeg (must be in system PATH)
- Mobile phone (Chrome recommended)

---

## 🚀 Setup Guide

### 1. Backend Setup (Django)

```bash
cd saferide_backend

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

python manage.py migrate

# Recommended for live streaming
python manage.py runserver 0.0.0.0:8000 --noreload
```

Backend URLs:

* [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* [http://127.0.0.1:8000/api/](http://127.0.0.1:8000/api/)

---

### 2. Frontend Setup (React)

```bash
cd saferide_frontend

npm install
# or
yarn install

npm start
```

Frontend URL:

* [http://localhost:3000/](http://localhost:3000/)

---

## 🎥 Live Streaming Setup

Pipeline:
Mobile → WebSocket → FFmpeg → RTSP → Django

The laptop runs backend + RTSP components.
The phone acts as the camera sender.

---

### Step A — Install MediaMTX (RTSP Server)
You need this to act as the "middleman" that broadcasts the video stream.

**For Windows:**

1. Go to the [MediaMTX Releases Page](https://github.com/bluenviron/mediamtx/releases).
2. Scroll down to "Assets" and download the file ending in `_windows_amd64.zip`.
3. Extract the zip file to a folder named `mediamtx` inside your project folder (e.g., `AISAFERIDE/mediamtx/`).
4. Inside you will see `mediamtx.exe`. **Do not run it yet**; we will run it in the "Run Order" steps.

**For macOS/Linux:**

- **Mac:** `brew install mediamtx`
- **Linux:** Download the `_linux_amd64.tar.gz` from the releases page, extract, and run the binary.

To start MediaMTX:

```bash
cd mediamtx
.\mediamtx.exe
```

Expected log:

```
INF [RTSP] listener opened on :8554 (TCP), :8000 (UDP/RTP), :8001 (UDP/RTCP)
```

---

### Step B — Install FFmpeg

FFmpeg is the engine that converts the raw video data into a streamable format.

**For Windows:**

1. **Download:** Go to [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/) and download `ffmpeg-git-full.7z`.
2. **Extract:** Unzip the file. You will see a `bin` folder containing `ffmpeg.exe`.
3. **Add to Path (Crucial):**
   - Copy the path to that `bin` folder (e.g., `C:\ffmpeg\bin`).
   - Press the **Windows Key** and type "Edit the system environment variables".
   - Click **Environment Variables**.
   - Under "System variables", find **Path** and click **Edit**.
   - Click **New** and paste the path to your `bin` folder.
   - Click OK on all windows.

4. **Verify:** Open a *new* terminal and type:

   `ffmpeg -version`

   If you see version info, it works.

**For macOS:**

- `brew install ffmpeg`

**For Linux (Ubuntu/Debian):**

- `sudo apt update && sudo apt install ffmpeg`

---

### Step C — Start WebSocket + FFmpeg Bridge

```bash
cd saferide_backend/streaming
python video_ws.py
```

Expected log:

```
[VIDEO WS] Listening on ws://0.0.0.0:9000
```

---

### Step D — Start Mobile Sender Host

```bash
cd saferide_backend/rtsp
python -m http.server 8080
```

Mobile page:

```
http://<LAPTOP_IP>:8080/mobile_sender.html
```

---

### Step E — Start Sending Video From Mobile

#### 1. Configure IP Address
Open `rtsp/mobile_sender.html` and ensure the WebSocket URL points to your laptop.
* **Automatic (Is currently used):**
    ```javascript
    const WS_URL = `ws://${window.location.hostname}:9000`;
    ```
* **Manual:** Run `ipconfig` on Windows to find your IPv4 address and hardcode it if needed.

#### 2. Enable Camera on HTTP (Crucial for Android)
Mobile Chrome blocks camera access on HTTP unless whitelisted.
1.  On your phone, go to: `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
2.  Set it to **Enabled**.
3.  In the text box, enter your laptop's origin: `http://<LAPTOP_IP>:8080` (e.g., `http://192.168.1.5:8080`)
4.  **Relaunch** Chrome completely.

#### 3. Start Streaming
1.  Navigate to: `http://<LAPTOP_IP>:8080/mobile_sender.html`
2.  Tap **Start Camera**.
3.  Allow permissions.

**✅ Expected Result:**
* Mobile video preview appears.
* `video_ws.py` logs: `Client connected` & `FFmpeg started`.
* MediaMTX logs: `publishing to path mobile`.

> **Troubleshooting:** If the camera works but WebSocket fails to connect, ensure your Laptop and Phone are on the **same Wi-Fi** and **Port 9000** is allowed through Windows Firewall.
---

# ✅ Correct Run Order (Live Demo)

### 1. Start MediaMTX 
```bash
# In Terminal 1
cd mediamtx
.\mediamtx.exe
```

### 2. Start WebSocket Bridge
```bash
# In Terminal 2
python saferide_backend/streaming/video_ws.py
```

### 3. Start Mobile HTTP Server
```bash
# In Terminal 3
cd saferide_backend/rtsp
python -m http.server 8080
```
### 4. Open mobile page and Start Camera

### 5. Start Django Backend
```bash
# In Terminal 4
cd saferide_backend
python manage.py runserver 0.0.0.0:8000 --noreload
```

### 6. Start React Frontend
```bash
# In Terminal 5
cd saferide_frontend
npm start
```

---

## ⚠️ Important Warning (Expected Logs)

If the backend starts before mobile streaming, you may see:

```
[rtsp @ ...] method DESCRIBE failed: 404 Not Found
❌ [RTSP] Could not open RTSP stream: rtsp://127.0.0.1:8554/mobile
```

This is expected.
Ignore it until the mobile sender starts streaming.

---

## 🔧 Troubleshooting

### Mobile camera permission denied

* Use Chrome on Android
* Ensure camera permission is allowed

### WebSocket not connecting

* Laptop and phone must be on same Wi-Fi
* Check correct IP in mobile sender page
* Ensure port 9000 is allowed in firewall

### RTSP 404 Not Found

* Mobile publisher is not running yet
* Restart mobile page and Start Camera

### React shows "Waiting for feed"

* Confirm backend endpoints are reachable:

  * [http://127.0.0.1:8000/api/stream/raw/](http://127.0.0.1:8000/api/stream/raw/)
  * [http://127.0.0.1:8000/api/stream/annotated/](http://127.0.0.1:8000/api/stream/annotated/)

---

## 📄 License

This project is licensed under the MIT License.
