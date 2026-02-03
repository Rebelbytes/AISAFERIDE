# views.py
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
import time
import os
import uuid
from datetime import datetime
import math
from .models import Violation
from .serializers import ViolationSerializer
from .license_plate_ocr import LicensePlateOCR
import easyocr
import re
import torch

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Load models (updated for merged 2wheeler model)
# Load YOLO model
model_path = os.path.join(settings.BASE_DIR.parent, "best.pt")
merged_2whe_model = YOLO(model_path)

merged_2whe_model.to(DEVICE)

# Initialize the OCR class globally
lp_ocr = LicensePlateOCR()

violation_classes = {
    0: "number_plate",
    1: "No Helmet",
    3: "Triple Riding",
    4: "Right Side",
    5: "Wrong Side",
    6: "Using Mobile",
    7: "Vehicle No License Plate"
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
    1: 0.1,
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
            violations.append((cls_id, conf, x1, y1, x2, y2))

    print(f"Total violations in frame: {len(violations)}")

    # Draw violations and nearest number plates
    drawn_plates = set()
    for cls_id, conf, x1, y1, x2, y2 in violations:
        label = violation_classes[cls_id]

        # Combine No Helmet + Using Mobile
        if cls_id == 1:
            for cls2, _, x1b, y1b, x2b, y2b in violations:
                if cls2 == 6:  # using_mobile
                    iou_x1, iou_y1 = max(x1, x1b), max(y1, y1b)
                    iou_x2, iou_y2 = min(x2, x2b), min(y2, y2b)
                    if iou_x1 < iou_x2 and iou_y1 < iou_y2:
                        label += " + Using Mobile"

        cv2.rectangle(frame, (x1, y1), (x2, y2), colors[cls_id], 2)
        cv2.putText(frame, label, (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[cls_id], 2)

        if plates:
            vx, vy = (x1 + x2) // 2, (y1 + y2) // 2
            nearest_plate = min(plates, key=lambda p: math.hypot(vx - (p[0] + p[2]) // 2, vy - (p[1] + p[3]) // 2))
            if nearest_plate not in drawn_plates:
                px1, py1, px2, py2 = nearest_plate
                cv2.rectangle(frame, (px1, py1), (px2, py2), colors[0], 2)
                cv2.putText(frame, "Number Plate", (px1, py1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[0], 2)
                drawn_plates.add(nearest_plate)

    # Draw any number plates that have no associated violations
    for px1, py1, px2, py2 in plates:
        if (px1, py1, px2, py2) not in drawn_plates:
            cv2.rectangle(frame, (px1, py1), (px2, py2), colors[0], 2)
            cv2.putText(frame, "Number Plate", (px1, py1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[0], 2)

    # Draw vehicle_no_license_plate boxes
    for x1, y1, x2, y2 in vehicle_no_plate:
        cv2.rectangle(frame, (x1, y1), (x2, y2), colors[7], 2)
        cv2.putText(frame, "Vehicle No License", (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[7], 2)

    return frame, violations, plates

def process_plate_all_methods(plate_crop, detection_id):
    """Process plate using only Tesseract and EasyOCR methods - LPRNet removed"""
    results = {}
    
    # 1. Aggressive Tesseract Only
    print(f"[Detection {detection_id}] Running Aggressive Tesseract...")
    tesseract_text, tesseract_confidence = process_with_aggressive_tesseract_only(plate_crop, detection_id)
    
    # Validate Tesseract output
    tesseract_valid, tesseract_format = is_valid_indian_plate_format(tesseract_text)
    if tesseract_valid:
        tesseract_confidence += 20
    
    results['tesseract'] = {
        'text': tesseract_text,
        'confidence': tesseract_confidence,
        'method': 'Tesseract',
        'is_valid': tesseract_valid,
        'format': tesseract_format
    }
    
    # 2. Aggressive EasyOCR Only
    print(f"[Detection {detection_id}] Running Aggressive EasyOCR...")
    easyocr_text, easyocr_confidence = process_with_aggressive_easyocr_only(plate_crop, detection_id)
    
    # Validate EasyOCR output
    easyocr_valid, easyocr_format = is_valid_indian_plate_format(easyocr_text)
    if easyocr_valid:
        easyocr_confidence += 20
    
    results['easyocr'] = {
        'text': easyocr_text,
        'confidence': easyocr_confidence,
        'method': 'EasyOCR',
        'is_valid': easyocr_valid,
        'format': easyocr_format
    }
    
    # 3. Combined Tesseract+EasyOCR (existing method)
    print(f"[Detection {detection_id}] Running Combined Tesseract+EasyOCR...")
    
    # Use the existing process_plate method which combines all approaches
    combined_text, combined_confidence = lp_ocr.process_plate(
        plate_crop, detection_id=detection_id,
        output_dir=os.path.join(settings.MEDIA_ROOT, "ocr_debug")
    )
    
    # Validate Combined output
    combined_valid, combined_format = is_valid_indian_plate_format(combined_text)
    if combined_valid:
        combined_confidence += 20
    
    results['combined'] = {
        'text': combined_text,
        'confidence': combined_confidence,
        'method': 'Combined',
        'is_valid': combined_valid,
        'format': combined_format
    }
    
    # Choose the best result
    best_result = None
    best_confidence = -1
    
    for method, result in results.items():
        if result['text'] == "UNREADABLE":
            continue
            
        if result['is_valid']:
            result['confidence'] += 30
        
        if result['confidence'] > best_confidence:
            best_result = result
            best_confidence = result['confidence']
    
    # Fallback: if no valid result, use combined if available
    if best_result is None and results['combined']['text'] != "UNREADABLE":
        best_result = results['combined']
        best_confidence = results['combined']['confidence']
    
    # Print all results for comparison
    print(f"\n=== OCR Results Comparison [Detection {detection_id}] ===")
    for method, result in results.items():
        status = "✓" if result['text'] != "UNREADABLE" else "✗"
        validity = f" [{result['format']}]" if result['is_valid'] else " [INVALID]"
        print(f"{status} {result['method']}: '{result['text']}'{validity} (Confidence: {result['confidence']:.2f}%)")
    
    if best_result:
        print(f"Selected: {best_result['method']} -> '{best_result['text']}'\n")
        return best_result['text'], best_result['confidence'], results
    else:
        print("No valid OCR results found\n")
        return "UNREADABLE", 0.0, results
    
def process_with_aggressive_tesseract_only(plate_crop, detection_id):
    """Process plate using only aggressive Tesseract OCR"""
    try:
        # Use the existing preprocessing from license_plate_ocr
        img_variants = lp_ocr.preprocess_plate_image(plate_crop)
        
        # Run aggressive Tesseract only
        tesseract_results = lp_ocr.aggressive_tesseract_ocr(img_variants)
        
        if not tesseract_results:
            return "UNREADABLE", 0.0
        
        # Score and pick best Tesseract result
        best_tesseract = None
        best_score = -1
        
        for result in tesseract_results:
            cleaned_text = result['text']
            score = lp_ocr.score_license_plate(cleaned_text, result['confidence'])
            
            if score > best_score:
                best_score = score
                best_tesseract = result
        
        if best_tesseract:
            return best_tesseract['text'], best_tesseract['confidence']
        else:
            return "UNREADABLE", 0.0
            
    except Exception as e:
        print(f"Aggressive Tesseract error: {e}")
        return "UNREADABLE", 0.0

def process_with_aggressive_easyocr_only(plate_crop, detection_id):
    """Process plate using only aggressive EasyOCR"""
    try:
        # Use the existing preprocessing from license_plate_ocr
        img_variants = lp_ocr.preprocess_plate_image(plate_crop)
        
        # Run aggressive EasyOCR only
        easyocr_results = lp_ocr.aggressive_easyocr(img_variants)
        
        if not easyocr_results:
            return "UNREADABLE", 0.0
        
        # Score and pick best EasyOCR result
        best_easyocr = None
        best_score = -1
        
        for result in easyocr_results:
            cleaned_text = result['text']
            score = lp_ocr.score_license_plate(cleaned_text, result['confidence'])
            
            if score > best_score:
                best_score = score
                best_easyocr = result
        
        if best_easyocr:
            return best_easyocr['text'], best_easyocr['confidence']
        else:
            return "UNREADABLE", 0.0
            
    except Exception as e:
        print(f"Aggressive EasyOCR error: {e}")
        return "UNREADABLE", 0.0

# REPLACE your existing is_valid_indian_plate_format function with this:
def is_valid_indian_plate_format(text):
    """Strict validation for Indian license plate formats with specific format matching"""
    if not text or text == "UNREADABLE":
        return False, "INVALID"
    
    # Remove spaces and special characters for validation
    clean_text = re.sub(r'[^A-Z0-9]', '', text.upper())
    
    # Check length
    if len(clean_text) < 8 or len(clean_text) > 10:
        return False, "INVALID_LENGTH"
    
    # Must start with 2 letters (state code)
    if len(clean_text) < 2 or not clean_text[:2].isalpha():
        return False, "INVALID_STATE_CODE"
    
    # Must contain numbers after state code
    if not any(c.isdigit() for c in clean_text[2:]):
        return False, "NO_NUMBERS"
    
    # Count letters and numbers
    letters = sum(c.isalpha() for c in clean_text)
    numbers = sum(c.isdigit() for c in clean_text)
    
    # Typical Indian plates have 3-4 letters and 4-6 numbers
    if letters < 3 or letters > 5 or numbers < 4 or numbers > 6:
        return False, "INVALID_CHARACTER_RATIO"
    
    # Check specific patterns
    format_match = check_specific_format(clean_text)
    if format_match:
        return True, format_match
    
    return True, "VALID_GENERIC"

def check_specific_format(text):
    """Check which specific Indian plate format the text matches"""
    clean_text = re.sub(r'[^A-Z0-9]', '', text.upper())
    
    # Standard modern formats (e.g., , KA01CD3456)
    if (len(clean_text) == 10 and 
        clean_text[:2].isalpha() and 
        clean_text[2:4].isdigit() and 
        clean_text[4:6].isalpha() and 
        clean_text[6:].isdigit()):
        return "STANDARD_MODERN"
    
    # Standard with single letter (e.g., TN09C1234, DL01S5678)
    if (len(clean_text) == 9 and 
        clean_text[:2].isalpha() and 
        clean_text[2:4].isdigit() and 
        clean_text[4:5].isalpha() and 
        clean_text[5:].isdigit()):
        return "STANDARD_SINGLE_LETTER"
    
    # Old format (e.g., MH041234, KA051567)
    if (len(clean_text) == 8 and 
        clean_text[:2].isalpha() and 
        clean_text[2:4].isdigit() and 
        clean_text[4:].isdigit()):
        return "OLD_FORMAT"
    
    # Bharat Series (e.g., 21BH1234A, 22BH5678AB)
    if "BH" in clean_text and len(clean_text) in [9, 10]:
        if clean_text[2:4] == "BH":
            return "BH_SERIES"
    
    # Check if it matches common patterns even if not perfect
    if (clean_text[:2].isalpha() and 
        any(c.isdigit() for c in clean_text[2:4]) and 
        any(c.isalpha() for c in clean_text[4:6]) and 
        any(c.isdigit() for c in clean_text[6:])):
        return "VALID_MIXED_FORMAT"
    
    return "VALID_BASIC"

class DetectView(APIView):
    def post(self, request):
        if "file" not in request.FILES:
            return Response({"error": "No file"}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.FILES["file"]
        fs = FileSystemStorage()
        filename = fs.save(uploaded_file.name, uploaded_file)
        filepath = fs.path(filename)

        is_video = filepath.lower().endswith(('.mp4', '.avi', '.mov'))
        is_image = filepath.lower().endswith(('.jpg', '.jpeg', '.png'))
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
            unique_violations = []  # Track unique violations with spatial and temporal tolerance
            spatial_tolerance = 80  # pixels tolerance for considering violations as the same spatially
            frame_gap = 15  # minimum frames between same violation type

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                frame_count += 1
                if frame_count % 2 != 0:
                    continue  # skip alternate frames

                processed_frame, violations_in_frame, plates = detect_frame(frame)

                for violation in violations_in_frame:
                    cls_id, conf, x1, y1, x2, y2 = violation
                    violation_dict = {
                        "type": violation_classes[cls_id],
                        "confidence": conf,
                        "bbox": (x1, y1, x2, y2),
                        "frame_number": frame_count
                    }

                    # Calculate center of current violation
                    current_center_x = (x1 + x2) // 2
                    current_center_y = (y1 + y2) // 2

                    # Check if this violation is similar to any previously detected
                    is_duplicate = False
                    for existing_violation in unique_violations:
                        existing_center_x = (existing_violation['bbox'][0] + existing_violation['bbox'][2]) // 2
                        existing_center_y = (existing_violation['bbox'][1] + existing_violation['bbox'][3]) // 2

                        # Check spatial proximity and temporal gap
                        spatial_match = (abs(current_center_x - existing_center_x) <= spatial_tolerance and
                                       abs(current_center_y - existing_center_y) <= spatial_tolerance)
                        temporal_gap = (frame_count - existing_violation['frame_number']) >= frame_gap

                        # If same type, spatially close, and not enough temporal separation
                        if (existing_violation['type'] == violation_dict['type'] and
                            spatial_match and not temporal_gap):
                            is_duplicate = True
                            break

                    if not is_duplicate:
                        # Find nearest license plate for this violation
                        license_plate_path = None
                        if plates:
                            vx, vy = (x1 + x2) // 2, (y1 + y2) // 2
                            nearest_plate = min(plates, key=lambda p: math.hypot(vx - (p[0] + p[2]) // 2, vy - (p[1] + p[3]) // 2))
                            px1, py1, px2, py2 = nearest_plate
                            # Crop the license plate from the frame
                            plate_crop = frame[py1:py2, px1:px2]
                            if plate_crop.size > 0:
                                plate_name = f"plate_{uuid.uuid4()}.jpg"
                                plate_path = os.path.join(settings.MEDIA_ROOT, "license_plates", plate_name)
                                os.makedirs(os.path.dirname(plate_path), exist_ok=True)
                                cv2.imwrite(plate_path, plate_crop)
                                license_plate_path = os.path.join("license_plates", plate_name)

                        # Add to unique violations list
                        unique_violations.append(violation_dict)

                        # Save frame image
                        frame_name = f"frame_{uuid.uuid4()}.jpg"
                        frame_path = os.path.join(settings.MEDIA_ROOT, "violation_frames", frame_name)
                        os.makedirs(os.path.dirname(frame_path), exist_ok=True)
                        cv2.imwrite(frame_path, processed_frame)

                        # Save each violation individually
                        violation_obj = Violation.objects.create(
                            frame_image=os.path.join("violation_frames", frame_name),
                            license_plate_image=license_plate_path,
                            violation_type=violation_dict["type"],
                            confidence=violation_dict["confidence"]
                        )
                        violations_created.append(violation_obj)

                out.write(processed_frame)

            cap.release()
            out.release()

        elif is_image:
            frame_count = 1
            frame = cv2.imread(filepath)
            if frame is None:
                return Response({"error": "Failed to read image"}, status=400)

            processed_frame, violations_in_frame, plates = detect_frame(frame)

            for violation in violations_in_frame:
                cls_id, conf, x1, y1, x2, y2 = violation
                violation_dict = {
                    "type": violation_classes[cls_id],
                    "confidence": conf,
                    "bbox": (x1, y1, x2, y2)
                }

                # Save frame image
                frame_name = f"frame_{uuid.uuid4()}.jpg"
                frame_path = os.path.join(settings.MEDIA_ROOT, "violation_frames", frame_name)
                os.makedirs(os.path.dirname(frame_path), exist_ok=True)
                cv2.imwrite(frame_path, processed_frame)

                # Find nearest license plate for this violation
                license_plate_path = None
                if plates:
                    vx, vy = (x1 + x2) // 2, (y1 + y2) // 2
                    nearest_plate = min(plates, key=lambda p: math.hypot(vx - (p[0] + p[2]) // 2, vy - (p[1] + p[3]) // 2))
                    px1, py1, px2, py2 = nearest_plate
                    # Crop the license plate from the frame
                    plate_crop = frame[py1:py2, px1:px2]
                    if plate_crop.size > 0:
                        plate_name = f"plate_{uuid.uuid4()}.jpg"
                        plate_path = os.path.join(settings.MEDIA_ROOT, "license_plates", plate_name)
                        os.makedirs(os.path.dirname(plate_path), exist_ok=True)
                        cv2.imwrite(plate_path, plate_crop)
                        license_plate_path = os.path.join("license_plates", plate_name)

                # Save each violation individually
                violation_obj = Violation.objects.create(
                    frame_image=os.path.join("violation_frames", frame_name),
                    license_plate_image=license_plate_path,
                    violation_type=violation_dict["type"],
                    confidence=violation_dict["confidence"]
                )
                violations_created.append(violation_obj)

        else:
            return Response({"error": "Unsupported file type"}, status=400)

        print(f"Total violations created: {len(violations_created)}")
        serializer = ViolationSerializer(violations_created, many=True)
        
        response_data = {
            "violations": serializer.data,
        }

        if is_video:
            response_data["annotated_video"] = f"{settings.MEDIA_URL}previews/output.mp4"

        return Response(response_data)

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

class AnalyticsView(APIView):
    def get(self, request):
        violations = Violation.objects.all()

        # Total violations
        total_violations = violations.count()

        # Violations by type for pie chart
        violations_by_type = []
        type_counts = {}
        for violation in violations:
            v_type = violation.violation_type
            type_counts[v_type] = type_counts.get(v_type, 0) + 1

        for v_type, count in type_counts.items():
            violations_by_type.append({
                'label': v_type,
                'value': count
            })

        # Violations by date
        violations_by_date = {}
        for violation in violations:
            date = violation.created_at.date().isoformat()
            violations_by_date[date] = violations_by_date.get(date, 0) + 1

        # Detailed violations for table
        detailed_violations = []
        for violation in violations.order_by('-created_at')[:10]:  # Last 10 violations
            detailed_violations.append({
                'violation_type': violation.violation_type,
                'timestamp': violation.created_at.isoformat(),
                'confidence': violation.confidence
            })

        data = {
            'total_violations': total_violations,
            'violations_by_type': violations_by_type,
            'violations_by_date': violations_by_date,
            'detailed_violations': detailed_violations
        }

        return Response(data)

class ProcessOCRView(APIView):
    pass
    def post(self, request):
        if "file" not in request.FILES:
            return Response({"error": "No file provided"}, status=400)
        
        uploaded_file = request.FILES["file"]
        
        # Read the image
        image_data = uploaded_file.read()
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return Response({"error": "Invalid image"}, status=400)
        
        # Generate a unique ID for this detection
        detection_id = f"ocr_{int(time.time())}"
        
        # Process with all OCR methods
        license_plate_text, ocr_score, ocr_comparison = process_plate_all_methods(image, detection_id)
        
        # Return results with format information
        response_data = {
            "best_result": license_plate_text,
            "confidence": ocr_score,
            "comparison": ocr_comparison,
            "results": []
        }
        
        # Add individual method results with format info
        for method, result in ocr_comparison.items():
            response_data["results"].append({
                "text": result.get('text', 'UNREADABLE'),
                "confidence": result.get('confidence', 0),
                "method": result.get('method', method),
                "is_valid": result.get('is_valid', False),
                "format": result.get('format', 'UNKNOWN')
            })
        
        return Response(response_data)