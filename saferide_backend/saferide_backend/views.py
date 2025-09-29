# saferide_backend/views.py
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
from roboflow import Roboflow
from inference_sdk import InferenceHTTPClient
import tempfile
import os
import uuid

# Load models (same as your Streamlit code)
model_dir = os.path.join(settings.BASE_DIR.parent, '')  # Root directory
try:
    helmet_model = YOLO(os.path.join(model_dir, "best.pt"))
    print("Helmet model loaded successfully")
except Exception as e:
    print(f"Error loading helmet model: {e}")
    helmet_model = None

try:
    triple_model = YOLO(os.path.join(model_dir, "tripleseat_best.pt"))
    print("Triple seat model loaded successfully")
except Exception as e:
    print(f"Error loading triple seat model: {e}")
    triple_model = None

API_KEY = "1hbOBH0LYKlgfhoyiNug"
try:
    rf = Roboflow(api_key=API_KEY)
    wrong_side_model = rf.workspace("samias-ml-space").project("wrong-way-driving-detection").version(2).model
    print("Wrong side model loaded successfully")
except Exception as e:
    print(f"Error loading wrong side model: {e}")
    wrong_side_model = None

CLIENT = InferenceHTTPClient(api_url="https://serverless.roboflow.com", api_key=API_KEY)
MOBILE_MODEL_ID = "mobile-jrr9b/3"

helmet_class_map = {0: "Number Plate", 1: "No Helmet", 2: "Good Helmet", 3: "Bad Helmet", 4: "Rider"}
colors = {"No Helmet": (0,0,255), "Good Helmet": (0,255,0), "Bad Helmet": (0,255,255), "Triple Seat": (255,0,0), "Wrong Side": (255,165,0), "Mobile Usage": (255,0,255)}

def detect_frame(frame, save_violations_dir=None):
    violation_types = []
    violation_images = []
    print(f"Processing frame of shape: {frame.shape}")  # Debug

    # Helmet detection
    if helmet_model:
        try:
            helmet_results = helmet_model(frame, conf=0.1)
            print(f"Helmet detections: {len(helmet_results[0].boxes)}")  # Debug
            for box in helmet_results[0].boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                label = helmet_class_map.get(cls_id, f"Unknown-{cls_id}")
                color = colors.get(label, (255,255,255))
                cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)
                cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                if label in ["No Helmet", "Bad Helmet"]:
                    violation_types.append({"type": label, "confidence": conf, "bbox": [x1, y1, x2, y2]})
                    if save_violations_dir:
                        cropped = frame[y1:y2, x1:x2]
                        if cropped.size > 0:
                            img_name = f"violation_{uuid.uuid4()}.jpg"
                            img_path = os.path.join(save_violations_dir, img_name)
                            cv2.imwrite(img_path, cropped)
                            violation_images.append(f"{settings.MEDIA_URL}violations/{img_name}")
                elif label == "Number Plate":
                    violation_types.append({"type": label, "confidence": conf, "bbox": [x1, y1, x2, y2]})
                    if save_violations_dir:
                        cropped = frame[y1:y2, x1:x2]
                        if cropped.size > 0:
                            img_name = f"violation_{uuid.uuid4()}.jpg"
                            img_path = os.path.join(save_violations_dir, img_name)
                            cv2.imwrite(img_path, cropped)
                            violation_images.append(f"{settings.MEDIA_URL}violations/{img_name}")
        except Exception as e:
            print(f"Helmet detection error: {e}")
    else:
        print("Helmet model not loaded")

    # Triple seat detection
    if triple_model:
        try:
            triple_results = triple_model(frame, conf=0.1)
            print(f"Triple detections: {len(triple_results[0].boxes)}")  # Debug
            for box in triple_results[0].boxes:
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                label = "Triple Seat"
                color = colors.get(label, (255,0,0))
                cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)
                cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                violation_types.append({"type": label, "confidence": conf, "bbox": [x1, y1, x2, y2]})
                if save_violations_dir:
                    cropped = frame[y1:y2, x1:x2]
                    if cropped.size > 0:
                        img_name = f"violation_{uuid.uuid4()}.jpg"
                        img_path = os.path.join(save_violations_dir, img_name)
                        cv2.imwrite(img_path, cropped)
                        violation_images.append(f"{settings.MEDIA_URL}violations/{img_name}")
        except Exception as e:
            print(f"Triple seat detection error: {e}")
    else:
        print("Triple seat model not loaded")

    # Wrong side detection using loaded Roboflow model
    if wrong_side_model:
        try:
            wrong_results = wrong_side_model.predict(frame, confidence=0.1, overlap=0.5)
            print(f"Wrong side result type: {type(wrong_results)}")
            if isinstance(wrong_results, dict) and 'predictions' in wrong_results:
                predictions = wrong_results['predictions']
            elif hasattr(wrong_results, '__len__') and len(wrong_results) > 0:
                if hasattr(wrong_results[0], 'predictions'):
                    predictions = wrong_results[0].predictions
                else:
                    predictions = wrong_results
            else:
                predictions = []
            print(f"Wrong side predictions: {len(predictions)}")  # Debug
            for pred in predictions:
                if pred.get('class') == 'wrong_side' or pred.get('class_name') == 'wrong_side':  # Assuming class name
                    conf = pred['confidence']
                    if 'bbox' in pred:
                        x, y, w, h = pred['bbox']
                        x1, y1 = int(x), int(y)
                        x2, y2 = int(x + w), int(y + h)
                    else:
                        x1, y1, x2, y2 = pred['x'], pred['y'], pred['x'] + pred['width'], pred['y'] + pred['height']
                    label = "Wrong Side"
                    color = colors.get(label, (255,165,0))
                    cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)
                    cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    violation_types.append({"type": label, "confidence": conf, "bbox": [x1, y1, x2, y2]})
                    if save_violations_dir:
                        cropped = frame[y1:y2, x1:x2]
                        if cropped.size > 0:
                            img_name = f"violation_{uuid.uuid4()}.jpg"
                            img_path = os.path.join(save_violations_dir, img_name)
                            cv2.imwrite(img_path, cropped)
                            violation_images.append(f"{settings.MEDIA_URL}violations/{img_name}")
        except Exception as e:
            print(f"Wrong side detection error: {e}")
    else:
        print("Wrong side model not loaded")

    # Mobile detection using InferenceHTTPClient
    if CLIENT:
        try:
            mobile_results = CLIENT.infer(frame, model_id=MOBILE_MODEL_ID)
            print(f"Mobile result type: {type(mobile_results)}")
            if 'predictions' in mobile_results:
                for pred in mobile_results['predictions']:
                    if pred['class'] == 'mobile':
                        conf = pred['confidence']
                        x, y, w, h = pred['x'], pred['y'], pred['width'], pred['height']
                        x1, y1 = int(x - w/2), int(y - h/2)
                        x2, y2 = int(x + w/2), int(y + h/2)
                        label = "Mobile Usage"
                        color = colors.get(label, (255,0,255))
                        cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)
                        cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                        violation_types.append({"type": label, "confidence": conf, "bbox": [x1, y1, x2, y2]})
                        if save_violations_dir:
                            cropped = frame[y1:y2, x1:x2]
                            if cropped.size > 0:
                                img_name = f"violation_{uuid.uuid4()}.jpg"
                                img_path = os.path.join(save_violations_dir, img_name)
                                cv2.imwrite(img_path, cropped)
                                violation_images.append(f"{settings.MEDIA_URL}violations/{img_name}")
        except Exception as e:
            print(f"Mobile detection error: {e}")
    else:
        print("Mobile client not loaded")

    print(f"Total violations: {len(violation_types)}")  # Debug
    return frame, violation_types, violation_images

class DetectView(APIView):
    def post(self, request):
        if 'file' not in request.FILES:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        vehicle_type = request.data.get('vehicle_type')
        if vehicle_type not in ['2 wheeler', '4 wheeler']:
            return Response({"error": "Only 2 wheeler and 4 wheeler supported"}, status=status.HTTP_400_BAD_REQUEST)
        
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
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                annotated_video_name = f"annotated_{uuid.uuid4()}.mp4"
                annotated_video_path = os.path.join(preview_dir, annotated_video_name)
                out = cv2.VideoWriter(annotated_video_path, fourcc, fps, (width, height))

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
                    processed_frame, frame_violations, _ = detect_frame(frame)  # No auto-save
                    violation_types.extend(frame_violations)

                    # Write annotated frame to output video
                    out.write(processed_frame)

                    if first_frame is None:
                        first_frame = processed_frame.copy()

                cap.release()
                out.release()

                yield f"Video processing complete: {frame_count} frames processed\n"

                # Add annotated video URL to response
                if os.path.exists(annotated_video_path) and os.path.getsize(annotated_video_path) > 0:
                    annotated_media.append(f"{settings.MEDIA_URL}previews/{annotated_video_name}")
                    yield "Annotated video saved successfully\n"
                else:
                    yield "WARNING: Video file may be empty\n"
                    # Fallback to first frame
                    if first_frame is not None:
                        img_name = f"preview_{uuid.uuid4()}.jpg"
                        img_path = os.path.join(preview_dir, img_name)
                        cv2.imwrite(img_path, first_frame)
                        annotated_media.append(f"{settings.MEDIA_URL}previews/{img_name}")
                        yield "Fallback preview frame saved\n"
            else:  # Image
                yield "Processing image...\n"
                frame = cv2.imread(filepath)
                if frame is not None:
                    processed_frame, frame_violations, _ = detect_frame(frame)  # No auto-save
                    violation_types = frame_violations
                    # Save annotated image
                    img_name = f"preview_{uuid.uuid4()}.jpg"
                    img_path = os.path.join(preview_dir, img_name)
                    cv2.imwrite(img_path, processed_frame)
                    annotated_media.append(f"{settings.MEDIA_URL}previews/{img_name}")
                    yield "Image processing complete\n"
                else:
                    yield "ERROR: Could not read image file\n"

            # Clean up uploaded file
            os.remove(filepath)
            yield "Upload file cleaned up\n"

            # Filter unique violation types
            unique_violations = []
            seen = set()
            for v in violation_types:
                key = v['type']
                if key not in seen:
                    seen.add(key)
                    unique_violations.append(v)

            # Send final JSON response
            import json
            final_data = {
                "status": "complete",
                "annotated_media": annotated_media,
                "violation_types": unique_violations,
                "violation_images": violation_images
            }
            yield f"DATA:{json.dumps(final_data)}\n"

        response = StreamingHttpResponse(process_stream(), content_type='text/plain')
        response['Cache-Control'] = 'no-cache'
        return response


class LiveDetectView(APIView):
    def post(self, request):
        vehicle_type = request.data.get('vehicle_type', '2 wheeler')
        if vehicle_type not in ['2 wheeler', '4 wheeler']:
            return Response({"error": "Only 2 wheeler and 4 wheeler supported"}, status=status.HTTP_400_BAD_REQUEST)
        
        base64_image = request.data.get('image_base64')
        if not base64_image:
            return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Decode base64 image
        import base64
        from io import BytesIO
        from PIL import Image as PILImage
        
        try:
            image_data = base64.b64decode(base64_image.split(',')[1])  # Remove data URL prefix if present
            pil_image = PILImage.open(BytesIO(image_data))
            frame = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        except Exception as e:
            return Response({"error": f"Invalid image data: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Process frame without saving violations automatically
        processed_frame, violation_types, violation_images = detect_frame(frame)
        
        # Encode processed frame as base64 for return
        _, buffer = cv2.imencode('.jpg', processed_frame)
        annotated_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Filter unique violations
        unique_violations = []
        seen = set()
        for v in violation_types:
            key = v['type']
            if key not in seen:
                seen.add(key)
                unique_violations.append(v)
        
        return Response({
            "annotated_image_base64": f"data:image/jpeg;base64,{annotated_base64}",
            "violation_types": unique_violations,
            "violation_images": violation_images
        }, status=status.HTTP_200_OK)

class SaveViolationView(APIView):
    def post(self, request):
        annotated_image_base64 = request.data.get('annotated_image_base64')
        annotated_image_url = request.data.get('annotated_image_url')
        violation = request.data.get('violation')  # {"type": "", "confidence": , "bbox": []}

        if (not annotated_image_base64 and not annotated_image_url) or not violation:
            return Response({"error": "Annotated image (base64 or url) and violation details required"}, status=status.HTTP_400_BAD_REQUEST)

        # Get annotated image
        import base64
        from io import BytesIO
        from PIL import Image as PILImage
        from datetime import datetime
        import requests

        try:
            if annotated_image_base64:
                image_data = base64.b64decode(annotated_image_base64.split(',')[1])
                pil_image = PILImage.open(BytesIO(image_data))
                frame = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            elif annotated_image_url:
                # Fetch image from URL
                response = requests.get(f"http://127.0.0.1:8000{annotated_image_url}")
                if response.status_code != 200:
                    return Response({"error": "Failed to fetch image from URL"}, status=status.HTTP_400_BAD_REQUEST)
                pil_image = PILImage.open(BytesIO(response.content))
                frame = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        except Exception as e:
            return Response({"error": f"Invalid image data: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # Get bbox
        bbox = violation.get('bbox', [])
        if len(bbox) != 4:
            return Response({"error": "Invalid bbox"}, status=status.HTTP_400_BAD_REQUEST)

        x1, y1, x2, y2 = bbox

        # Crop the violation
        cropped = frame[y1:y2, x1:x2]
        if cropped.size == 0:
            return Response({"error": "Invalid crop"}, status=status.HTTP_400_BAD_REQUEST)

        # Create dated folder
        today = datetime.now().strftime('%Y-%m-%d')
        violations_dir = os.path.join(settings.MEDIA_ROOT, 'violations', today)
        os.makedirs(violations_dir, exist_ok=True)

        # Save cropped image
        img_name = f"{violation['type'].replace(' ', '_')}_{uuid.uuid4()}.jpg"
        img_path = os.path.join(violations_dir, img_name)
        cv2.imwrite(img_path, cropped)

        image_url = f"{settings.MEDIA_URL}violations/{today}/{img_name}"

        return Response({"image_url": image_url}, status=status.HTTP_201_CREATED)

class SavedViolationsView(APIView):
    def get(self, request):
        import os
        from datetime import datetime

        violations_dir = os.path.join(settings.MEDIA_ROOT, 'violations')
        if not os.path.exists(violations_dir):
            return Response({"violations": []}, status=status.HTTP_200_OK)

        violations_by_date = {}
        for date_folder in sorted(os.listdir(violations_dir), reverse=True):
            date_path = os.path.join(violations_dir, date_folder)
            if os.path.isdir(date_path):
                violations_by_date[date_folder] = []
                for filename in sorted(os.listdir(date_path), reverse=True):
                    if filename.endswith('.jpg'):
                        violations_by_date[date_folder].append({
                            "filename": filename,
                            "url": f"{settings.MEDIA_URL}violations/{date_folder}/{filename}",
                            "timestamp": os.path.getmtime(os.path.join(date_path, filename))
                        })

        return Response({"violations_by_date": violations_by_date}, status=status.HTTP_200_OK)

def home(request):
    return JsonResponse({
        "message": "🚦 Welcome to SafeRide AI API",
        "endpoints": {
            "register": "/api/register/",
            "login": "/api/login/",
            "dashboard": "/api/dashboard/",
            "detect": "/api/detect/",
            "saved-violations": "/api/saved-violations/"
        }
    })
