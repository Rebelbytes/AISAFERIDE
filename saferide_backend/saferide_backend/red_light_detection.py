# Red Light Detection Module
import numpy as np
import cv2
import pytesseract
import re
from collections import deque
from PIL import Image
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Load cascade classifier for license plate detection
# Try multiple paths to find the cascade file
cascade_paths = [
    os.path.join(settings.BASE_DIR.parent, "haarcascade_russian_plate_number.xml"),
    os.path.join(settings.BASE_DIR, "haarcascade_russian_plate_number.xml"),
    "haarcascade_russian_plate_number.xml",
]

license_plate_cascade = None
for cascade_path in cascade_paths:
    if os.path.exists(cascade_path):
        license_plate_cascade = cv2.CascadeClassifier(cascade_path)
        if not license_plate_cascade.empty():
            print(f"✓ Cascade classifier loaded from: {cascade_path}")
            break

if license_plate_cascade is None or license_plate_cascade.empty():
    print(f"⚠ Warning: Cascade classifier not found. Tried: {cascade_paths}")
    print("Make sure 'haarcascade_russian_plate_number.xml' exists in the project root.")


class RedLightDetector:
    def __init__(self):
        self.y_start_queue = deque(maxlen=10)
        self.y_end_queue = deque(maxlen=10)
        self.detected_plates = set()
        self.signal_state = "green"
        self.frame_count = 0
        self.red_signal_start = None

    def update_signal_state(self, frame_count, total_frames_per_cycle=155):
        """
        Simulate traffic signal cycling: Green (90 frames) -> Yellow (5 frames) -> Red (60 frames)
        """
        cycle_position = frame_count % total_frames_per_cycle
        if cycle_position < 90:
            self.signal_state = "green"
        elif cycle_position < 95:
            self.signal_state = "yellow"
        else:
            self.signal_state = "red"
            if self.red_signal_start is None:
                self.red_signal_start = frame_count

    def detect_white_line(self, frame, slope1=-0.2, intercept1=920, slope2=-0.2, intercept2=770, slope3=-0.8, intercept3=2420):
        """
        Detect the stop line in the frame
        Returns: (processed_frame, mask_line, y_capture)
        """
        frame_org = frame.copy()

        def line1(x):
            return slope1 * x + intercept1

        def line2(x):
            return slope2 * x + intercept2

        def line3(y):
            return slope3 * y + intercept3

        height, width = frame.shape[:2]

        # Build masks for Hough line detection
        mask1 = frame.copy()
        for x in range(width):
            y_line = line1(x)
            mask1[int(max(0, min(height - 1, y_line))):, x] = 0

        mask2 = mask1.copy()
        for x in range(width):
            y_line = line2(x)
            mask2[:int(max(0, min(height - 1, y_line))), x] = 0

        mask3 = mask2.copy()
        for y in range(height):
            x_line = line3(y)
            mask3[y, :int(max(0, min(width - 1, x_line)))] = 0

        gray = cv2.cvtColor(mask3, cv2.COLOR_BGR2GRAY)
        blurred_gray = cv2.GaussianBlur(gray, (7, 7), 0)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray_clahe = clahe.apply(blurred_gray)

        edges = cv2.Canny(gray_clahe, 30, 100)
        dilated_edges = cv2.dilate(edges, None, iterations=1)
        edges = cv2.erode(dilated_edges, None, iterations=1)

        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=160, maxLineGap=5)

        x_start = 0
        x_end = width - 1

        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                slope = (y2 - y1) / (x2 - x1 + np.finfo(float).eps)
                intercept = y1 - slope * x1
                y_start = int(slope * x_start + intercept)
                y_end = int(slope * x_end + intercept)
                self.y_start_queue.append(y_start)
                self.y_end_queue.append(y_end)

        avg_y_start = int(sum(self.y_start_queue) / len(self.y_start_queue)) if self.y_start_queue else height // 2
        avg_y_end = int(sum(self.y_end_queue) / len(self.y_end_queue)) if self.y_end_queue else height // 2

        # Create detection mask
        mask = np.zeros_like(frame)
        line_start_ratio = 0.32
        x_start_adj = x_start + int(line_start_ratio * (x_end - x_start))
        avg_y_start_adj = avg_y_start + int(line_start_ratio * (avg_y_end - avg_y_start))
        cv2.line(mask, (x_start_adj, avg_y_start_adj), (x_end, avg_y_end), (255, 255, 255), 4)

        for channel_index in range(3):
            frame[mask[:, :, channel_index] == 255, channel_index] = 255

        # Compute average slope/intercept for capture line
        slope_avg = (avg_y_end - avg_y_start) / (x_end - x_start + np.finfo(float).eps)
        intercept_avg = avg_y_start - slope_avg * x_start

        # Move line slightly above bottom
        uplift_offset = 50
        mask_line = np.copy(frame_org)
        for x in range(width):
            y_line = slope_avg * x + intercept_avg - uplift_offset
            y_clip = int(max(0, min(height - 1, y_line)))
            mask_line[:y_clip, x] = 0

        y_capture = int((slope_avg * (width // 2) + intercept_avg) - uplift_offset)

        # Draw detection zone
        y_start_line = max(0, int(intercept_avg - uplift_offset))
        y_end_line = max(0, int(slope_avg * (width - 1) + intercept_avg - uplift_offset))
        cv2.line(frame, (0, y_start_line), (width - 1, y_end_line), (0, 255, 255), 2)

        zone_h = 300
        y1_zone = max(0, y_capture)
        y2_zone = min(height - 1, y_capture + zone_h)
        cv2.rectangle(frame, (0, y1_zone), (width - 1, y2_zone), (255, 0, 0), 2)

        return frame, mask_line, y_capture

    def extract_license_plate(self, frame, mask_line, y_capture, band_height=220):
        """
        Extract license plates from the detection zone
        Returns: (frame_with_detection, license_plate_images)
        """
        height, width = frame.shape[:2]
        y1 = max(0, y_capture)
        y2 = min(height, y_capture + band_height)
        band = mask_line[y1:y2, :]

        gray_band = cv2.cvtColor(band, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray_band = clahe.apply(cv2.GaussianBlur(gray_band, (5, 5), 0))
        kernel = np.ones((2, 2), np.uint8)
        gray_band = cv2.erode(gray_band, kernel, iterations=1)

        license_plate_images = []
        
        # Check if cascade classifier is loaded
        if license_plate_cascade is None or license_plate_cascade.empty():
            print("⚠ Cascade classifier not available. Skipping plate detection.")
            return frame, license_plate_images
        
        try:
            license_plates = license_plate_cascade.detectMultiScale(gray_band, scaleFactor=1.07, minNeighbors=8, minSize=(60, 20))
        except cv2.error as e:
            print(f"⚠ Error in cascade detection: {e}")
            return frame, license_plate_images

        for (x_plate, y_plate, w_plate, h_plate) in license_plates:
            top_left = (x_plate, y1 + y_plate)
            bottom_right = (x_plate + w_plate, y1 + y_plate + h_plate)
            cv2.rectangle(frame, top_left, bottom_right, (0, 255, 0), 3)
            plate_img = gray_band[y_plate:y_plate + h_plate, x_plate:x_plate + w_plate]
            license_plate_images.append(plate_img)

        return frame, license_plate_images

    def apply_ocr_to_image(self, license_plate_image):
        """
        Apply OCR to extract license plate text
        Returns: license_plate_text
        """
        try:
            _, img = cv2.threshold(license_plate_image, 120, 255, cv2.THRESH_BINARY)
            pil_img = Image.fromarray(img)
            full_text = pytesseract.image_to_string(pil_img, config='--psm 6')
            return full_text.strip()
        except:
            return ""

    def is_valid_indian_plate(self, text):
        """
        Validate if text matches Indian license plate format
        Example: DL 01 AB 1234
        """
        pattern = r"^[A-Z]{2}\s[0-9]{1,2}\s?[A-Z]{1,2}\s[0-9]{3,4}$"
        return bool(re.match(pattern, text))

    def detect_frame(self, frame, frame_number):
        """
        Main detection function for red light violations
        Returns: (processed_frame, violations_list)
        """
        violations = []

        # Update signal state based on frame number
        self.update_signal_state(frame_number)
        
        # Debug: Log signal state every 10 frames
        if frame_number % 10 == 0:
            logger.info(f"[Frame {frame_number}] Signal: {self.signal_state}")

        # Add signal state to frame
        font = cv2.FONT_HERSHEY_SIMPLEX
        signal_color = (0, 255, 0) if self.signal_state == "green" else (0, 255, 255) if self.signal_state == "yellow" else (0, 0, 255)
        message = f"Signal Status: {self.signal_state.upper()}"
        cv2.putText(frame, message, (20, 40), font, 1.2, signal_color, 3)

        # Detect stop line
        frame, mask_line, y_capture = self.detect_white_line(frame)
        logger.debug(f"[Frame {frame_number}] Stop line detected at y={y_capture}")

        # Extract plates only during red signal
        if self.signal_state == "red":
            logger.info(f"[Frame {frame_number}] RED SIGNAL - Checking for violations")
            frame, license_plate_images = self.extract_license_plate(frame, mask_line, y_capture)
            logger.info(f"[Frame {frame_number}] Found {len(license_plate_images)} license plates")

            for idx, license_plate_image in enumerate(license_plate_images):
                text = self.apply_ocr_to_image(license_plate_image)
                logger.info(f"[Frame {frame_number}] Plate {idx+1} OCR result: '{text}'")

                # Validate and store violations
                if text:
                    is_valid = self.is_valid_indian_plate(text)
                    is_duplicate = text in self.detected_plates
                    logger.info(f"[Frame {frame_number}] Plate '{text}' - Valid: {is_valid}, Duplicate: {is_duplicate}")
                    
                    if is_valid and not is_duplicate:
                        self.detected_plates.add(text)
                        violations.append({
                            "type": "Red Light Jumping",
                            "confidence": 0.95,
                            "plate_number": text,
                            "signal_state": self.signal_state,
                            "frame_number": frame_number
                        })
                        logger.warning(f"[RED LIGHT VIOLATION] Plate: {text} at Frame: {frame_number}")
                else:
                    logger.debug(f"[Frame {frame_number}] OCR returned empty text")

        return frame, violations
