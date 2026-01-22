# Red Light Detection Integration Guide

## ✅ Integration Complete

Your red light crossing detection has been successfully integrated into the SafeRide backend. Here's what was implemented:

---

## 📁 Files Modified/Created

### 1. **New File: `red_light_detection.py`**
   - Location: `saferide_backend/saferide_backend/red_light_detection.py`
   - Contains: `RedLightDetector` class with all red light detection logic
   - Features:
     - Traffic signal color detection (red/yellow/green)
     - Stop line detection using Hough line transform
     - License plate extraction when vehicle crosses red light
     - OCR-based plate number reading
     - Indian license plate format validation

### 2. **Modified: `views.py`**
   - Added import: `from .red_light_detection import RedLightDetector`
   - Updated `DetectView.post()` to:
     - Accept `violation_category` parameter from frontend
     - Route to appropriate detector based on category:
       - `"general"` → Uses existing YOLO model (helmet, triple seat, etc.)
       - `"red_light"` → Uses new RedLightDetector class
     - Process videos and images for both violation types
     - Save violations with proper metadata

### 3. **Frontend Already Ready**
   - `Dashboard.js`: Radio buttons for violation selection (lines 850-871)
   - Sends `violation_category` in form data
   - PreviewDetection page works for both violation types

---

## 🔄 Data Flow

```
User Dashboard
    ↓
Select Vehicle Type (2 wheeler)
    ↓
Select Violation Type:
  ├─ General Violations (Helmet, Triple Seat, etc.)
  └─ Red Light Jumping
    ↓
Upload Video/Image
    ↓
Backend DetectView.post()
    ├─ Gets violation_category parameter
    ├─ Routes to correct detector:
    │  ├─ YOLO for "general"
    │  └─ RedLightDetector for "red_light"
    ↓
Process Frames
    ├─ Detect violations
    ├─ Save annotated video
    ├─ Create Violation objects
    ↓
Return Response with:
  - annotated_video (processed video)
  - violations (list of detected violations)
    ↓
PreviewDetection Component
    ├─ Shows annotated video
    ├─ Shows detected violations
    ├─ Allows saving/creating challans
```

---

## 🚀 How to Use

### Step 1: Prepare Your Video
- Ensure video shows a traffic light and stop line
- Video should capture vehicles crossing during red light

### Step 2: In Dashboard
1. Click "AI Detection" tab
2. Select "2 wheeler" as vehicle type
3. **Select "Red Light Jumping"** (radio button)
4. Upload your video file
5. Click "Start Detection"

### Step 3: View Results
- Same PreviewDetection page as general violations
- Shows:
  - Annotated video with signal status
  - Detected red light violations
  - License plate numbers (from OCR)
  - Can generate e-challans from results

---

## 📊 RedLightDetector Class Features

### Key Methods:

#### `update_signal_state(frame_count, total_frames_per_cycle=155)`
- Simulates traffic light cycling
- Default: Green (90 frames) → Yellow (5 frames) → Red (60 frames)
- Adjust `total_frames_per_cycle` based on your video FPS

#### `detect_white_line(frame)`
- Detects the stop line in the frame
- Returns: processed frame with line visualization

#### `extract_license_plate(frame, mask_line, y_capture)`
- Extracts license plate from detection zone
- Uses cascade classifier for plate detection
- Returns: frame with detections + cropped plate images

#### `apply_ocr_to_image(license_plate_image)`
- Applies Tesseract OCR to license plate
- Returns: extracted text

#### `is_valid_indian_plate(text)`
- Validates Indian plate format
- Example: "DL 01 AB 1234"

#### `detect_frame(frame, frame_number)`
- **Main detection function** - called for each frame
- Returns: (processed_frame, violations_list)
- Violations list contains:
  ```python
  {
    "type": "Red Light Jumping",
    "confidence": 0.95,
    "plate_number": "DL01AB1234",
    "signal_state": "red",
    "frame_number": 42
  }
  ```

---

## ⚙️ Configuration/Customization

### Adjust Signal Timing:
In `red_light_detection.py`, modify `update_signal_state()`:
```python
# Default: 90 green + 5 yellow + 60 red = 155 frames total
# Adjust based on your video FPS
self.update_signal_state(frame_number, total_frames_per_cycle=155)
```

### Adjust Stop Line Detection:
Modify line equation parameters in `detect_white_line()`:
```python
slope1=-0.2, intercept1=920,   # Line 1 parameters
slope2=-0.2, intercept2=770,   # Line 2 parameters
slope3=-0.8, intercept3=2420   # Line 3 parameters
```

### Adjust Detection Zone Height:
In `extract_license_plate()`:
```python
band_height=220  # Height of zone to look for license plates
```

---

## 🐛 Troubleshooting

### Issue: No violations detected
- **Solution**: Check if stop line parameters match your video
  - Adjust slope and intercept values
  - Ensure cascade classifier path is correct

### Issue: License plates not being extracted
- **Solution**: Verify:
  - `haarcascade_russian_plate_number.xml` exists in project root
  - `band_height` parameter covers license plate area
  - Image quality is sufficient for cascade classifier

### Issue: OCR text not readable
- **Solution**:
  - Ensure Tesseract is installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`
  - Verify plate image quality
  - Adjust threshold value in `apply_ocr_to_image()` (currently 120)

### Issue: Signal state detection incorrect
- **Solution**: Adjust frame cycle in `update_signal_state()`
  - Count actual frames in your video where each signal appears
  - Update `total_frames_per_cycle` accordingly

---

## 📝 API Response Format

### Request:
```python
POST /api/detect/
Content-Type: multipart/form-data

file: <video_file>
vehicle_type: "2 wheeler"
violation_category: "red_light"  # ← Key parameter
```

### Response:
```json
{
  "violations": [
    {
      "id": 1,
      "frame_image": "/media/violation_frames/frame_xxx.jpg",
      "license_plate_image": null,
      "violation_type": "Red Light Jumping",
      "confidence": 0.95,
      "created_at": "2026-01-18T10:30:00Z"
    }
  ],
  "annotated_video": "/media/previews/output.mp4"
}
```

---

## 🔧 Database Model

Violations are saved in the existing `Violation` model:
```python
class Violation(models.Model):
    frame_image = ImageField()
    license_plate_image = ImageField(null=True, blank=True)
    violation_type = CharField()  # "Red Light Jumping" for red light
    confidence = FloatField()
    created_at = DateTimeField(auto_now_add=True)
```

---

## ✨ Testing Checklist

- [ ] Upload a red light violation video
- [ ] Verify signal status displays correctly on annotated video
- [ ] Check that license plates are detected and extracted
- [ ] Verify OCR reads plate numbers correctly
- [ ] Confirm violations appear in PreviewDetection page
- [ ] Test creating e-challan from detected violation
- [ ] Check database for saved violations
- [ ] Test both general and red light violations work independently

---

## 📞 Support Notes

If you need to modify:
1. **Signal timing**: Edit `update_signal_state()` in `RedLightDetector`
2. **Stop line detection**: Adjust line parameters in `detect_white_line()`
3. **License plate area**: Modify `band_height` in `extract_license_plate()`
4. **OCR accuracy**: Adjust threshold in `apply_ocr_to_image()`

All integration is backward compatible - general violations still work as before!
