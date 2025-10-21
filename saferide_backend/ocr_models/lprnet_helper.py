import torch
import cv2
import numpy as np
import os
import re
from django.conf import settings

# Try to import LPRNet with proper error handling
try:
    from .LPRNet import LPRNet
    LPRNET_IMPORTED = True
except ImportError as e:
    print(f"LPRNet import error: {e}")
    LPRNET_IMPORTED = False

# Device setup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Character mapping
CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
BLANK = "-"
idx_to_char = {i: c for i, c in enumerate(CHARS + BLANK)}
num_classes = len(CHARS) + 1

# Global model instance
_lprnet_model = None

def initialize_lprnet(model_path=None):
    """Initialize LPRNet model globally"""
    global _lprnet_model
    
    if not LPRNET_IMPORTED:
        print("LPRNet not imported - skipping initialization")
        return None
    
    if _lprnet_model is not None:
        return _lprnet_model
    
    if model_path is None:
        # Try to find the model in different possible locations
        possible_paths = [
            "D:\\PyProject\\MajorProject\\AISAFERIDE\\best_lprnet.pth",
            os.path.join(settings.BASE_DIR, "best_lprnet.pth"),
            os.path.join(settings.BASE_DIR, "ocr_models", "best_lprnet.pth"),
            os.path.join(settings.BASE_DIR.parent, "best_lprnet.pth"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                model_path = path
                break
        else:
            print("LPRNet model file not found in any known location")
            return None
    
    try:
        print(f"Loading LPRNet model from: {model_path}")
        
        # FIXED: Correct parameter order
        _lprnet_model = LPRNet(
            phase='test',           # FIRST parameter
            class_num=num_classes,  # SECOND parameter  
            dropout_rate=0,         # THIRD parameter
            lpr_max_len=8          # FOURTH parameter
        )
        
        # Load state dict
        state_dict = torch.load(model_path, map_location=device)
        
        # Handle different state dict formats
        if 'state_dict' in state_dict:
            state_dict = state_dict['state_dict']
        elif 'model' in state_dict:
            state_dict = state_dict['model']
        
        # Remove 'module.' prefix if present
        new_state_dict = {}
        for k, v in state_dict.items():
            if k.startswith('module.'):
                new_state_dict[k[7:]] = v
            else:
                new_state_dict[k] = v
        
        _lprnet_model.load_state_dict(new_state_dict)
        _lprnet_model.eval()
        _lprnet_model.to(device)
        
        print("LPRNet model loaded successfully")
        return _lprnet_model
        
    except Exception as e:
        print(f"Error loading LPRNet model: {e}")
        _lprnet_model = None
        return None

def enhance_plate_image(plate_img):
    """Dramatically enhance plate image for better OCR"""
    try:
        # Convert to grayscale if needed
        if len(plate_img.shape) == 3:
            gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_img.copy()
        
        # 1. Super Resolution - Upscale the image
        height, width = gray.shape
        if height < 50 or width < 100:
            # Upscale for better recognition
            scale = 3.0  # 3x upscale
            new_height, new_width = int(height * scale), int(width * scale)
            gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # 2. Noise removal
        gray = cv2.medianBlur(gray, 3)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # 3. Extreme contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # 4. Sharpening
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        # 5. Multiple thresholding variants
        _, binary_otsu = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        adaptive = cv2.adaptiveThreshold(sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY, 11, 2)
        
        # Return multiple variants for OCR to try
        return {
            'otsu': binary_otsu,
            'adaptive': adaptive,
            'sharpened': sharpened
        }
        
    except Exception as e:
        print(f"Plate enhancement error: {e}")
        return {'default': plate_img}

def decode_predictions(preds):
    """Decode model predictions with CTC-style collapsing"""
    result = []
    prev = -1
    for p in preds:
        if p != prev and p != len(CHARS):  # Skip blanks and repeated chars
            result.append(idx_to_char[p])
        prev = p
    return ''.join(result)

def is_plausible_license_plate(text):
    """Check if text looks like a plausible license plate (not too strict)"""
    if not text or len(text) < 6:
        return False
    
    # Remove spaces and special chars
    clean_text = re.sub(r'[^A-Z0-9]', '', text.upper())
    
    # Basic checks
    if len(clean_text) < 6 or len(clean_text) > 12:
        return False
    
    # Should have both letters and numbers
    has_letters = any(c.isalpha() for c in clean_text)
    has_numbers = any(c.isdigit() for c in clean_text)
    
    if not (has_letters and has_numbers):
        return False
    
    # Check character distribution (not too many repeated chars)
    if len(set(clean_text)) < len(clean_text) * 0.5:  # Too many repeats
        return False
    
    return True

def predict_lprnet(plate_img):
    """Predict license plate text using LPRNet with better error handling"""
    global _lprnet_model
    
    if _lprnet_model is None:
        initialize_lprnet()
    
    if _lprnet_model is None:
        return "UNREADABLE", 0.0
    
    try:
        # Enhanced preprocessing
        enhanced_variants = enhance_plate_image(plate_img)
        
        best_text = "UNREADABLE"
        best_confidence = 0.0
        
        # Try multiple enhanced variants
        for variant_name, enhanced_img in enhanced_variants.items():
            try:
                # Convert to 3 channels if needed
                if len(enhanced_img.shape) == 2:
                    enhanced_img = cv2.cvtColor(enhanced_img, cv2.COLOR_GRAY2BGR)
                
                # Resize to LPRNet input size
                plate_resized = cv2.resize(enhanced_img, (94, 24))
                
                # Normalize
                plate_resized = plate_resized.astype(np.float32) / 255.0
                plate_resized = np.transpose(plate_resized, (2, 0, 1))  # HWC -> CHW
                plate_tensor = torch.from_numpy(plate_resized).unsqueeze(0).to(device)
                
                with torch.no_grad():
                    logits = _lprnet_model(plate_tensor)
                    
                    # Handle different logits shapes
                    if len(logits.shape) == 3:
                        probs, preds = torch.max(logits, dim=2)
                        preds = preds.squeeze(0).cpu().numpy()
                    else:
                        preds = torch.argmax(logits, dim=1).squeeze(0).cpu().numpy()
                    
                    # Decode predictions
                    raw_text = decode_predictions(preds)
                    
                    # Filter garbage output
                    if is_plausible_license_plate(raw_text):
                        confidence = min(len(raw_text) * 10, 30.0)
                        if confidence > best_confidence:
                            best_text = raw_text
                            best_confidence = confidence
                            print(f"LPRNet {variant_name}: '{raw_text}' (Confidence: {confidence:.1f}%)")
            
            except Exception as e:
                continue
        
        if best_text != "UNREADABLE":
            return best_text, best_confidence
        else:
            return "UNREADABLE", 0.0
                
    except Exception as e:
        print(f"LPRNet prediction error: {e}")
        return "UNREADABLE", 0.0

# Initialize on import
initialize_lprnet()