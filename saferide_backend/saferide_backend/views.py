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
import math
from .models import Violation
from .serializers import ViolationSerializer
# Load models (updated for merged 2wheeler model)
# Load YOLO model
model_dir = os.path.join(settings.BASE_DIR.parent, "")
merged_2whe_model = YOLO(os.path.join(model_dir, "best.pt"))

violation_classes = {
    0: "number_plate",
    1: "no_helmet",
    3: "triple_riding",
    4: "right_side",
    5: "wrong_side",
    6: "using_mobile",
    7: "vehicle_no_license_plate"
}

colors = {
    0: (255, 0, 0),
    1: (0, 0, 255),
    3: (0, 255, 255),
    4: (255, 255, 0),
    5: (255, 0, 255),
    6: (128, 0, 128),
    7: (0, 255, 255)
}

conf_thresholds = {
    0: 0.2,
    1: 0.6,
    3: 0.2,
    4: 0.1,
    5: 0.1,
    6: 0.2,
    7: 0.15
}

def center(x1, y1, x2, y2):
    return ((x1 + x2) // 2, (y1 + y2) // 2)

def detect_frame(frame):
    violations = []
    plates = []
    vehicle_no_plate = []

    results = merged_2whe_model(frame, conf=0.1)[0]

    print(f"Detected {len(results.boxes)} objects")

    for box in results.boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        print(f"Class ID: {cls_id}, Conf: {conf}")

        if cls_id in conf_thresholds and conf < conf_thresholds[cls_id]:
            print(f"Skipped due to low confidence: {conf} < {conf_thresholds[cls_id]}")
            continue

        if cls_id == 0:
            plates.append((x1, y1, x2, y2))
        elif cls_id == 7:
            vehicle_no_plate.append((x1, y1, x2, y2))
        elif cls_id in [1, 3, 4, 5, 6]:
            violations.append({
                "type": violation_classes[cls_id],  # string label
                "confidence": conf,
                "bbox": (x1, y1, x2, y2)
            })
            print(f"Added violation: {violation_classes[cls_id]}")

    print(f"Total violations in frame: {len(violations)}")

    if not violations:
        return frame, []

    # Draw violations on frame
    drawn_plates = set()
    for v in violations:
        x1, y1, x2, y2 = v["bbox"]
        cls_id = list(violation_classes.keys())[list(violation_classes.values()).index(v["type"])]
        cv2.rectangle(frame, (x1, y1), (x2, y2), colors[cls_id], 2)
        cv2.putText(frame, v["type"], (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[cls_id], 2)

        if plates:
            vx, vy = (x1+x2)//2, (y1+y2)//2
            nearest_plate = min(plates, key=lambda p: math.hypot(vx - (p[0]+p[2])//2, vy - (p[1]+p[3])//2))
            if nearest_plate not in drawn_plates:
                px1, py1, px2, py2 = nearest_plate
                cv2.rectangle(frame, (px1, py1), (px2, py2), colors[0], 2)
                cv2.putText(frame, "Number Plate", (px1, py1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[0], 2)
                drawn_plates.add(nearest_plate)

    return frame, violations

class DetectView(APIView):
    def post(self, request):
        if "file" not in request.FILES:
            return Response({"error": "No file"}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.FILES["file"]
        fs = FileSystemStorage()
        filename = fs.save(uploaded_file.name, uploaded_file)
        filepath = fs.path(filename)

        is_video = filepath.lower().endswith(('.mp4', '.avi', '.mov'))
        violations_created = []

        if is_video:
            cap = cv2.VideoCapture(filepath)
            if not cap.isOpened():
                return Response({"error": "Cannot open video"}, status=400)

            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            preview_dir = os.path.join(settings.MEDIA_ROOT, 'previews')
            os.makedirs(preview_dir, exist_ok=True)
            video_out_path = os.path.join(preview_dir, "output.mp4")
            out = cv2.VideoWriter(video_out_path, cv2.VideoWriter_fourcc(*'H264'), fps, (width, height))


            frame_count = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                frame_count += 1
                if frame_count % 2 != 0:
                    continue  # skip alternate frames

                processed_frame, violations_in_frame = detect_frame(frame)

                for violation in violations_in_frame:
                    # Save frame image
                    frame_name = f"frame_{uuid.uuid4()}.jpg"
                    frame_path = os.path.join(settings.MEDIA_ROOT, "violation_frames", frame_name)
                    os.makedirs(os.path.dirname(frame_path), exist_ok=True)
                    cv2.imwrite(frame_path, processed_frame)

                    # Save each violation individually
                    violation_obj = Violation.objects.create(
                        frame_image=os.path.join("violation_frames", frame_name),
                        violation_type=violation["type"],
                        confidence=violation["confidence"]
                    )
                    violations_created.append(violation_obj)

                out.write(processed_frame)

            cap.release()
            out.release()
        else:
            return Response({"error": "Only video files supported"}, status=400)

        print(f"Total violations created: {len(violations_created)}")
        serializer = ViolationSerializer(violations_created, many=True)
        return Response({
            "violations": serializer.data,
            "annotated_video": f"{settings.MEDIA_URL}previews/output.mp4"
        })


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

class ViolationsListView(APIView):
    def get(self, request):
        violations = Violation.objects.all().order_by('-created_at')
        serializer = ViolationSerializer(violations, many=True)
        return Response(serializer.data)

