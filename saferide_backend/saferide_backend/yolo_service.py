import cv2
import math
import os
import torch
from ultralytics import YOLO
from django.conf import settings

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {DEVICE}")

# Load YOLO model once
model_path = os.path.join(settings.BASE_DIR.parent, "best.pt")
merged_2whe_model = YOLO(model_path)

merged_2whe_model.to(DEVICE)

def warmup_model():
    """
    Warms up YOLO once at startup to avoid first-frame lag during live detection.

    Returns:
        None
    """
    try:
        # Create a dummy tensor input for warmup (matches YOLO input format)
        dummy = torch.zeros((1, 3, 640, 640), device=DEVICE)

        # Run one inference silently
        merged_2whe_model.predict(dummy, verbose=False)

        print(f"✅ [YOLO] Warmup completed on {DEVICE}")

    except Exception as e:
        print("⚠️ [YOLO] Warmup failed:", str(e))
warmup_model()

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

def detect_frame(frame):
    """
    Returns:
      annotated_frame (numpy image)
      violations_list (list of dicts: type/confidence/bbox)
    """
    violations = []
    plates = []
    vehicle_no_plate = []

    results = merged_2whe_model.predict(
    frame,
    conf=0.1,
    device=DEVICE,
    verbose=False
    )[0]

    for box in results.boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        if cls_id in conf_thresholds and conf < conf_thresholds[cls_id]:
            continue

        if cls_id == 0:
            plates.append((x1, y1, x2, y2))
        elif cls_id == 7:
            vehicle_no_plate.append((x1, y1, x2, y2))
        elif cls_id in [1, 3, 4, 5, 6]:
            violations.append((cls_id, conf, x1, y1, x2, y2))

    drawn_plates = set()

    for cls_id, conf, x1, y1, x2, y2 in violations:
        label = violation_classes.get(cls_id, str(cls_id))

        cv2.rectangle(frame, (x1, y1), (x2, y2), colors[cls_id], 2)
        cv2.putText(frame, label, (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[cls_id], 2)

        if plates:
            vx, vy = (x1 + x2) // 2, (y1 + y2) // 2
            nearest_plate = min(
                plates,
                key=lambda p: math.hypot(vx - (p[0] + p[2]) // 2, vy - (p[1] + p[3]) // 2)
            )

            if nearest_plate not in drawn_plates:
                px1, py1, px2, py2 = nearest_plate
                cv2.rectangle(frame, (px1, py1), (px2, py2), colors[0], 2)
                cv2.putText(frame, "Number Plate", (px1, py1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[0], 2)
                drawn_plates.add(nearest_plate)

    # draw unlinked plates
    for px1, py1, px2, py2 in plates:
        if (px1, py1, px2, py2) not in drawn_plates:
            cv2.rectangle(frame, (px1, py1), (px2, py2), colors[0], 2)
            cv2.putText(frame, "Number Plate", (px1, py1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[0], 2)

    # draw no license plate
    for x1, y1, x2, y2 in vehicle_no_plate:
        cv2.rectangle(frame, (x1, y1), (x2, y2), colors[7], 2)
        cv2.putText(frame, "Vehicle No License", (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[7], 2)

    # convert violations to frontend-friendly format
    violation_dicts = []
    for cls_id, conf, x1, y1, x2, y2 in violations:
        violation_dicts.append({
            "type": violation_classes.get(cls_id, "unknown"),
            "confidence": conf,
            "bbox": [x1, y1, x2, y2]
        })

    return frame, violation_dicts, plates
