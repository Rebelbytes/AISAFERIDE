from django.http import JsonResponse, StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO
from inference_sdk import InferenceHTTPClient
import tempfile
import os
import uuid
from datetime import datetime

# Load models (updated for merged 2wheeler model)
model_dir = os.path.join(settings.BASE_DIR.parent, '')  # Root directory
try:
    merged_2whe_model = YOLO(os.path.join(model_dir, "2whe_merged.pt"))
    print("Merged 2wheeler model loaded successfully")
except Exception as e:
    print(f"Error loading merged 2wheeler model: {e}")
    merged_2whe_model = None

# Red light model will be added later
red_light_model = None  # Placeholder


# Updated class map based on merged model
violation_class_map = {
    0: "number_plate",
    1: "no_helmet",
    2: "rider",
    3: "Triple_riding",
    4: "right-side",
    5: "wrong-side",
    6: "USING_MOBILE",
    7: "Vehicle_no_license_plate"
}

colors = {
    "no_helmet": (0,0,255),
    "Triple_riding": (255,0,0),
    "wrong-side": (255,165,0),
    "USING_MOBILE": (255,0,255),
    "number_plate": (0,255,0),
    "Red Light Jumping": (0,255,255)
}

def detect_frame(frame, violation_category='general', vehicle_type='2 wheeler', save_violations_dir=None):
    violation_types = []
    violation_images = []
    print(f"Processing frame of shape: {frame.shape}")  # Debug

    if violation_category == 'general':
        # Use merged model for general violations
        if merged_2whe_model:
            try:
                results = merged_2whe_model(frame, conf=0.1)
                print(f"Detections: {len(results[0].boxes)}")  # Debug
                for box in results[0].boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    label = violation_class_map.get(cls_id, f"Unknown-{cls_id}")
                    color = colors.get(label, (255,255,255))
                    cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)
                    cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    # Check if it's a violation
                    if label in ["no_helmet", "Triple_riding", "wrong-side", "USING_MOBILE", "number_plate"]:
                        violation_type_folder = label.replace('_', ' ').title()
                        violation_types.append({"type": violation_type_folder, "confidence": conf, "bbox": [x1, y1, x2, y2]})
                        if save_violations_dir:
                            cropped = frame[y1:y2, x1:x2]
                            if cropped.size > 0:
                                date = datetime.now().strftime('%Y-%m-%d')
                                img_name = f"violation_{uuid.uuid4()}.jpg"
                                img_dir = os.path.join(save_violations_dir, date, violation_type_folder)
                                os.makedirs(img_dir, exist_ok=True)
                                img_path = os.path.join(img_dir, img_name)
                                cv2.imwrite(img_path, cropped)
                                violation_images.append(f"{settings.MEDIA_URL}violations/{date}/{violation_type_folder}/{img_name}")
            except Exception as e:
                print(f"Merged model detection error: {e}")
        else:
            print("Merged model not loaded")

    print(f"Total violations: {len(violation_types)}")  # Debug
    return frame, violation_types, violation_images

class DetectView(APIView):
    def post(self, request):
        if 'file' not in request.FILES:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        vehicle_type = request.data.get('vehicle_type')
        if vehicle_type not in ['2 wheeler', '4 wheeler']:
            return Response({"error": "Only 2 wheeler and 4 wheeler supported"}, status=status.HTTP_400_BAD_REQUEST)

        violation_category = request.data.get('violation_category', 'general')

        uploaded_file = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(uploaded_file.name, uploaded_file)
        filepath = fs.path(filename)

        preview_dir = os.path.join(settings.MEDIA_ROOT, 'previews')
        violations_dir = os.path.join(settings.MEDIA_ROOT, 'violations')
        os.makedirs(preview_dir, exist_ok=True)
        os.makedirs(violations_dir, exist_ok=True)

        def process_stream():
            annotated_media = []
            violation_types = []
            violation_images = []
            is_video = filepath.lower().endswith(('.mp4', '.avi', '.mov'))

            if is_video:
                yield "Starting video processing...\n"
                cap = cv2.VideoCapture(filepath)
                if not cap.isOpened():
                    yield "ERROR: Could not open video file\n"
                    return

                # Get video properties
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                yield f"Video loaded: {total_frames} frames at {fps} FPS ({width}x{height})\n"

                # Prepare output video writer
                fourcc = cv2.VideoWriter_fourcc(*'avc1')
                date = datetime.now().strftime('%Y-%m-%d')
                annotated_video_name = f"annotated_{uuid.uuid4()}.mp4"
                annotated_video_path = os.path.join(preview_dir, date, annotated_video_name)
                os.makedirs(os.path.dirname(annotated_video_path), exist_ok=True)
                out = cv2.VideoWriter(annotated_video_path, fourcc, fps, (width, height))

                print(f"VideoWriter initialized with fps={fps}, size=({width},{height}), codec='XVID'")  # Debug

                frame_count = 0
                first_frame = None

                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    frame_count += 1
                    progress = (frame_count / total_frames) * 100
                    yield f"Processing frame {frame_count}/{total_frames} ({progress:.1f}%)\n"

                    # Annotate frame with detections
                    processed_frame, frame_violations, _ = detect_frame(frame, violation_category, vehicle_type)  # Pass params
                    violation_types.extend(frame_violations)

                    if processed_frame is None or processed_frame.size == 0:
                        print(f"Warning: processed_frame is empty at frame {frame_count}")
                        continue

                    # Write annotated frame to output video
                    out.write(processed_frame)

                    if first_frame is None:
                        first_frame = processed_frame.copy()

                cap.release()
                out.release()

                yield f"Video processing complete: {frame_count} frames processed\n"

                # Add annotated video URL to response
                if os.path.exists(annotated_video_path) and os.path.getsize(annotated_video_path) > 0:
                    full_url = f"{settings.MEDIA_URL}previews/{date}/{annotated_video_name}"
                    annotated_media.append(full_url)
                    yield f"Annotated video saved successfully: {full_url}\n"
                else:
                    yield "WARNING: Video file may be empty\n"
                    # Fallback to first frame
                    if first_frame is not None:
                        img_name = f"preview_{uuid.uuid4()}.jpg"
                        img_path = os.path.join(preview_dir, img_name)
                        cv2.imwrite(img_path, first_frame)
                        full_url = f"http://127.0.0.1:8000{settings.MEDIA_URL}previews/{img_name}"
                        annotated_media.append(full_url)
                        yield f"Fallback preview frame saved: {full_url}\n"

                # Final JSON response
                import json
                final_data = {
                    "status": "complete",
                    "annotated_media": annotated_media,
                    "violation_types": violation_types,
                    "violation_images": violation_images
                }
                yield "===PROCESSING COMPLETE===\n"
                yield f"DATA:{json.dumps(final_data)}\n"

        response = StreamingHttpResponse(process_stream(), content_type='text/plain')
        response['Cache-Control'] = 'no-cache'
        return response

def home(request):
    return JsonResponse({"message": "Welcome to Saferide Backend"})

class LiveDetectView(APIView):
    def get(self, request):
        return Response({"message": "Live detection endpoint"})

class SaveViolationView(APIView):
    def post(self, request):
        return Response({"message": "Violation saved"})

class SavedViolationsView(APIView):
    def get(self, request):
        violations_dir = os.path.join(settings.MEDIA_ROOT, 'violations')
        violations_by_date = {}

        if os.path.exists(violations_dir):
            for root, dirs, files in os.walk(violations_dir):
                for file in files:
                    if file.endswith(('.jpg', '.png', '.jpeg')):
                        filepath = os.path.join(root, file)
                        # Get modification time as timestamp
                        timestamp = os.path.getmtime(filepath)
                        date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                        url = f"{settings.MEDIA_URL}violations/{os.path.relpath(filepath, violations_dir).replace(os.sep, '/')}"

                        if date not in violations_by_date:
                            violations_by_date[date] = []

                        violations_by_date[date].append({
                            "url": url,
                            "filename": file,
                            "timestamp": int(timestamp)
                        })

        return Response({"violations_by_date": violations_by_date})

