# license_plate_ocr.py
import cv2
import numpy as np
from ultralytics import YOLO
import pytesseract
import easyocr
import os
import re
import torch
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LicensePlateOCR:
    def __init__(self):
        # Initialize OCR processor
        self.easyocr_reader = None
        self.init_ocr_engines()

        # Valid Indian State Codes (expanded with common misreads)
        self.VALID_STATE_CODES = [
            "AN", "AP", "AR", "AS", "BR", "CH", "CG", "DD", "DL", "DN", 
            "GA", "GJ", "HR", "HP", "JK", "JH", "KA", "KL", "LD", "MP", 
            "MH", "MN", "ML", "MZ", "NL", "OD", "PB", "PY", "RJ", "SK", 
            "TN", "TS", "TR", "UP", "UK", "WB",
            # Common misreads that should be accepted
            "IN", "TH", "MH", "AP", "TN", "KA", "KL", "DL", "HR", "PB",
            "MH", "MP", "UP", "RJ", "GJ", "WB"
        ]

        # License plate patterns (prioritized for Indian plates)
        self.plate_patterns = {
            'indian_standard': r'^[A-Z]{2}\s?\d{1,2}\s?[A-Z]{1,3}\s?\d{1,4}$',
            'two_line_numeric': r'^\d{2}-?[A-Z]\d\s+\d{4}$',
            'indian_old': r'^[A-Z]{2,3}\s?\d{3,4}$',
            'generic': r'^[A-Z0-9\s\-]{4,15}$'
        }

        # Common character substitutions for OCR errors
        self.char_substitutions = {
            '0': 'O', '1': 'I', '5': 'S', '8': 'B',
            'O': '0', 'I': '1', 'S': '5', 'B': '8'
        }

    def init_ocr_engines(self):
        """Initialize available OCR engines"""
        try:
            self.easyocr_reader = easyocr.Reader(['en'], gpu=True)
            logging.info("EasyOCR initialized successfully")
        except Exception as e:
            logging.error(f"EasyOCR initialization failed: {e}")
            self.easyocr_reader = None

    def super_resolution_enhance(self, plate_img):
        """Aggressive enhancement for low-resolution plates"""
        try:
            if len(plate_img.shape) == 3:
                gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
            else:
                gray = plate_img.copy()
            
            # Get original dimensions
            h, w = gray.shape
            
            # If too small, upscale significantly
            if h < 30 or w < 80:
                scale = max(100/h, 200/w)  # Scale to at least 100x200
                new_h, new_w = int(h * scale), int(w * scale)
                gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            
            # Multiple enhancement techniques
            variants = {}
            
            # 1. CLAHE for extreme contrast
            clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
            clahe_img = clahe.apply(gray)
            variants['clahe'] = clahe_img
            
            # 2. Bilateral filter for noise
            bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
            variants['bilateral'] = bilateral
            
            # 3. Sharpening
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(gray, -1, kernel)
            variants['sharpened'] = sharpened
            
            # 4. Multiple thresholding methods
            _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            variants['otsu'] = otsu
            
            adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                           cv2.THRESH_BINARY, 11, 2)
            variants['adaptive'] = adaptive
            
            # 5. Morphological operations to connect broken characters
            kernel = np.ones((2, 1), np.uint8)
            morph = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel)
            variants['morph'] = morph
            
            # 6. Denoising
            denoised = cv2.fastNlMeansDenoising(gray)
            variants['denoised'] = denoised
            
            return variants
            
        except Exception as e:
            logging.error(f"Super resolution error: {e}")
            return {'original': plate_img}

    def has_valid_state_code(self, text):
        """Check if text starts with a valid Indian state code (relaxed)"""
        if not text or len(text) < 2:
            return False
        
        # Extract first two characters
        state_code = text[:2].upper()
        return state_code in self.VALID_STATE_CODES

    def preprocess_plate_image(self, img):
        """Enhanced preprocessing for license plates with super resolution"""
        # First apply super resolution
        enhanced_variants = self.super_resolution_enhance(img)
        return enhanced_variants

    def correct_common_errors(self, text):
        """Correct common OCR errors aggressively"""
        if not text:
            return ""
        
        text = text.upper().strip()
        
        # Common pattern corrections for Indian plates
        corrections = [
            (r'[Il1]', 'I'),  # I, l, 1 confusion
            (r'[O0]', '0'),   # O vs 0
            (r'[S5]', '5'),   # S vs 5
            (r'[B8]', '8'),   # B vs 8
            (r'[Z2]', '2'),   # Z vs 2
            (r'[T7]', '7'),   # T vs 7
        ]
        
        for pattern, replacement in corrections:
            text = re.sub(pattern, replacement, text)
        
        return text

    def aggressive_tesseract_ocr(self, img_variants):
        """Very aggressive Tesseract OCR with multiple configs"""
        results = []
        
        # Extensive config combinations
        configs = [
            # Single line configs
            {'psm': 7, 'oem': 3, 'whitelist': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-./'},
            {'psm': 8, 'oem': 3, 'whitelist': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-./'},
            {'psm': 13, 'oem': 3, 'whitelist': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-./'},
            # Single word configs  
            {'psm': 8, 'oem': 3, 'whitelist': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-./'},
            {'psm': 10, 'oem': 3, 'whitelist': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-./'},
            # Sparse text configs
            {'psm': 11, 'oem': 3, 'whitelist': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-./'},
            {'psm': 12, 'oem': 3, 'whitelist': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-./'},
        ]
        
        for variant_name, img in img_variants.items():
            for config in configs:
                try:
                    custom_config = f"--oem {config['oem']} --psm {config['psm']}"
                    if 'whitelist' in config:
                        custom_config += f" -c tessedit_char_whitelist={config['whitelist']}"
                    
                    # Try with different page segmentation modes
                    data = pytesseract.image_to_data(img, config=custom_config, output_type=pytesseract.Output.DICT)
                    
                    # Extract all text with confidence > 0
                    text_items = []
                    conf_items = []
                    
                    for i in range(len(data['text'])):
                        text = data['text'][i].strip()
                        conf = int(data['conf'][i])
                        if text and conf > 0:
                            text_items.append(text)
                            conf_items.append(conf)
                    
                    if text_items:
                        combined_text = ' '.join(text_items)
                        avg_conf = np.mean(conf_items) if conf_items else 0
                        
                        # Clean and correct the text
                        cleaned_text = self.correct_common_errors(combined_text)
                        
                        if len(cleaned_text.replace(' ', '')) >= 4:  # Reduced from 6 to 4
                            results.append({
                                'engine': 'tesseract',
                                'variant': variant_name,
                                'config': f"psm{config['psm']}",
                                'text': cleaned_text,
                                'confidence': avg_conf,
                                'raw_text': combined_text
                            })
                            
                except Exception as e:
                    continue
        
        return results

    def tesseract_ocr(self, img_variants):
        """Optimized Tesseract OCR with relaxed state-code filtering"""
        results = []
        configs = [
            {'psm': 7, 'oem': 3, 'whitelist': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-./'},
            {'psm': 6, 'oem': 3, 'whitelist': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-./'},
            {'psm': 4, 'oem': 3, 'whitelist': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-./'},
        ]

        for variant_name, img in img_variants.items():
            for config in configs:
                try:
                    custom_config = f"--oem {config['oem']} --psm {config['psm']} -c tessedit_char_whitelist={config['whitelist']}"
                    data = pytesseract.image_to_data(img, config=custom_config, output_type=pytesseract.Output.DICT)
                    
                    # Extract text with confidence > 0 (more lenient)
                    text_items = []
                    conf_items = []
                    
                    for i in range(len(data['text'])):
                        text = data['text'][i].strip()
                        conf = int(data['conf'][i])
                        if text and conf > 0:  # Reduced from 10 to 0
                            text_items.append(text)
                            conf_items.append(conf)
                    
                    if text_items:
                        combined_text = ' '.join(text_items)
                        avg_conf = np.mean(conf_items) if conf_items else 0

                        if len(combined_text.replace(' ', '').replace('-', '')) >= 4:  # Reduced from 6 to 4
                            cleaned_text = self.clean_and_format_text(combined_text, avg_conf)
                            
                            # RELAXED STATE FILTERING: Accept more results
                            if self.has_valid_state_code(cleaned_text):
                                valid_state = True
                                state_bonus = 20
                            else:
                                valid_state = False
                                state_bonus = 0
                                # Don't filter out - just don't give bonus
                            
                            results.append({
                                'engine': 'tesseract',
                                'variant': variant_name,
                                'config': f"psm{config['psm']}_oem{config['oem']}",
                                'text': combined_text,
                                'cleaned_text': cleaned_text,
                                'confidence': avg_conf + state_bonus,  # Apply bonus to confidence
                                'lines': len(text_items),
                                'valid_state': valid_state
                            })
                except Exception as e:
                    logging.warning(f"Tesseract OCR failed for variant {variant_name}: {e}")
                    continue
        return results

    def aggressive_easyocr(self, img_variants):
        """Aggressive EasyOCR with multiple parameter sets"""
        results = []
        
        param_sets = [
            {'width_ths': 0.1, 'height_ths': 0.1, 'min_size': 5, 'text_threshold': 0.1},
            {'width_ths': 0.3, 'height_ths': 0.3, 'min_size': 10, 'text_threshold': 0.2},
            {'width_ths': 0.5, 'height_ths': 0.5, 'min_size': 15, 'text_threshold': 0.3},
            {'width_ths': 0.7, 'height_ths': 0.7, 'min_size': 20, 'text_threshold': 0.4},
        ]
        
        for variant_name, img in img_variants.items():
            for params in param_sets:
                try:
                    ocr_result = self.easyocr_reader.readtext(
                        img,
                        allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-./',
                        **params
                    )
                    
                    if ocr_result:
                        # Combine all detected text
                        all_text = ' '.join([result[1] for result in ocr_result if result[1].strip()])
                        confidences = [result[2] for result in ocr_result if result[1].strip()]
                        avg_conf = np.mean(confidences) if confidences else 0
                        
                        if all_text and len(all_text.replace(' ', '')) >= 4:
                            cleaned_text = self.correct_common_errors(all_text)
                            results.append({
                                'engine': 'easyocr',
                                'variant': variant_name,
                                'config': f"width{params['width_ths']}",
                                'text': cleaned_text,
                                'confidence': avg_conf * 100,
                                'raw_text': all_text
                            })
                            
                except Exception as e:
                    continue
        
        return results

    def easyocr_ocr(self, img_variants):
        """Enhanced EasyOCR processing with relaxed state-code filtering"""
        results = []
        if not self.easyocr_reader:
            return results

        param_sets = [
            {'width_ths': 0.3, 'height_ths': 0.3, 'paragraph': False, 'min_size': 10},
            {'width_ths': 0.5, 'height_ths': 0.5, 'paragraph': False, 'min_size': 15},
            {'width_ths': 0.7, 'height_ths': 0.7, 'paragraph': False, 'min_size': 20},
            {'width_ths': 0.1, 'height_ths': 0.1, 'paragraph': False, 'min_size': 5},  # More aggressive
        ]

        for variant_name, img in img_variants.items():
            for i, params in enumerate(param_sets):
                try:
                    ocr_result = self.easyocr_reader.readtext(
                        img,
                        allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-/.',
                        **params
                    )
                    
                    if ocr_result:
                        # Combine all text
                        all_text = ' '.join([result[1] for result in ocr_result if result[1].strip()])
                        confidences = [result[2] for result in ocr_result if result[1].strip()]
                        avg_conf = np.mean(confidences) if confidences else 0
                        
                        if len(all_text.replace(' ', '').replace('-', '')) >= 6:
                            cleaned_text = self.clean_and_format_text(all_text, avg_conf * 100)
                            
                            # RELAXED STATE FILTERING
                            if self.has_valid_state_code(cleaned_text):
                                valid_state = True
                                state_bonus = 20
                            else:
                                valid_state = False
                                state_bonus = 0
                            
                            results.append({
                                'engine': 'easyocr',
                                'variant': variant_name,
                                'config': f'params_{i}',
                                'text': all_text,
                                'cleaned_text': cleaned_text,
                                'confidence': (avg_conf * 100) + state_bonus,
                                'lines': len(ocr_result),
                                'valid_state': valid_state
                            })
                except Exception as e:
                    logging.warning(f"EasyOCR failed for variant {variant_name}: {e}")
                    continue

        return results

    def group_text_by_lines(self, data):
        """Group OCR text data by lines"""
        valid_items = []
        for i in range(len(data['text'])):
            if int(data['conf'][i]) > 0:
                text = data['text'][i].strip()
                if text:
                    valid_items.append({
                        'text': text,
                        'conf': int(data['conf'][i]),
                        'left': int(data['left'][i]),
                        'top': int(data['top'][i]),
                        'width': int(data['width'][i]),
                        'height': int(data['height'][i])
                    })

        if not valid_items:
            return []

        valid_items.sort(key=lambda x: x['top'])
        lines = []
        current_line = []
        line_threshold = 25

        for item in valid_items:
            if not current_line:
                current_line.append(item)
            else:
                avg_top = np.mean([x['top'] for x in current_line])
                if abs(item['top'] - avg_top) <= line_threshold:
                    current_line.append(item)
                else:
                    current_line.sort(key=lambda x: x['left'])
                    lines.append({
                        'texts': [x['text'] for x in current_line],
                        'confidences': [x['conf'] for x in current_line],
                        'y_pos': avg_top
                    })
                    current_line = [item]

        if current_line:
            current_line.sort(key=lambda x: x['left'])
            avg_top = np.mean([x['top'] for x in current_line])
            lines.append({
                'texts': [x['text'] for x in current_line],
                        'confidences': [x['conf'] for x in current_line],
                        'y_pos': avg_top
                    })

        return lines

    def combine_lines_intelligently(self, text_lines):
        """Combine text lines for plate formats"""
        if len(text_lines) == 1:
            return ' '.join(text_lines[0]['texts'])
        elif len(text_lines) == 2:
            line1 = ''.join(text_lines[0]['texts'])
            line2 = ''.join(text_lines[1]['texts'])
            return f"{line1} {line2}"
        else:
            all_texts = []
            for line in text_lines:
                line_text = ' '.join(line['texts'])
                if line_text.strip():
                    all_texts.append(line_text)
            return ' '.join(all_texts)

    def group_easyocr_results(self, ocr_result):
        """Group EasyOCR results by lines"""
        if not ocr_result:
            return []

        valid_results = []
        for result in ocr_result:
            if result[1].strip():
                bbox = result[0]
                y_center = np.mean([point[1] for point in bbox])
                x_center = np.mean([point[0] for point in bbox])
                valid_results.append({
                    'text': result[1].strip(),
                    'conf': result[2],
                    'x_center': x_center,
                    'y_center': y_center
                })

        if not valid_results:
            return []

        valid_results.sort(key=lambda x: x['y_center'])
        lines = []
        current_line = []
        line_threshold = 30

        for result in valid_results:
            if not current_line:
                current_line.append(result)
            else:
                avg_y = np.mean([x['y_center'] for x in current_line])
                if abs(result['y_center'] - avg_y) <= line_threshold:
                    current_line.append(result)
                else:
                    current_line.sort(key=lambda x: x['x_center'])
                    lines.append(current_line)
                    current_line = [result]

        if current_line:
            current_line.sort(key=lambda x: x['x_center'])
            lines.append(current_line)

        return lines

    def format_grouped_results(self, grouped_results):
        """Format grouped OCR results"""
        if len(grouped_results) == 1:
            return ' '.join([result['text'] for result in grouped_results[0]])
        elif len(grouped_results) == 2:
            line1 = ''.join([result['text'] for result in grouped_results[0]])
            line2 = ''.join([result['text'] for result in grouped_results[1]])
            return f"{line1} {line2}"
        else:
            all_lines = []
            for line in grouped_results:
                line_text = ' '.join([result['text'] for result in line])
                if line_text.strip():
                    all_lines.append(line_text)
            return ' '.join(all_lines)

    def clean_and_format_text(self, text, confidence):
        """Clean and format OCR text dynamically based on confidence"""
        if not text:
            return ""

        text = text.upper().strip()
        text = re.sub(r'[^A-Z0-9\s\-]', '', text)

        # Apply common error corrections
        text = self.correct_common_errors(text)

        # Dynamic correction based on confidence
        if confidence < 50:
            # For low-confidence OCR, be more aggressive with corrections
            text = re.sub(r'[O0]', '0', text)
            text = re.sub(r'[I1]', '1', text)
            text = re.sub(r'[S5]', '5', text)
        else:
            # For high-confidence OCR, trust the output more but fix common errors
            if re.match(r'^\d{2}-[A-Z]\d', text):
                text = re.sub(r'[O0]', '0', text)
                text = re.sub(r'[I1]', '1', text)
            elif re.match(r'^[A-Z]{2}\s?\d{1,2}', text):
                text = re.sub(r'[0O]', 'O', text, 2)
                text = re.sub(r'[I1]', 'I', text, 2)

        # Format spacing and dashes
        text = re.sub(r'\s*-\s*', '-', text)
        text = re.sub(r'(\d{2})-?([A-Z]\d)\s*(\d{4})', r'\1-\2 \3', text)
        text = re.sub(r'([A-Z]{2})\s*(\d{2})\s*([A-Z]{1,2})\s*(\d{4})', r'\1 \2 \3 \4', text)

        return text.strip()

    def score_license_plate(self, text, confidence):
        """Score license plate text with relaxed criteria"""
        if not text or len(text.replace(' ', '').replace('-', '')) < 4:  # Reduced from 6 to 4
            return 0

        score = 0
        clean_text = text.replace(' ', '').replace('-', '')

        # Length scoring (relaxed)
        if 6 <= len(clean_text) <= 12:
            score += 20
        elif 4 <= len(clean_text) <= 15:  # More lenient
            score += 10

        # Character mix (relaxed)
        letters = sum(c.isalpha() for c in clean_text)
        numbers = sum(c.isdigit() for c in clean_text)
        
        if letters >= 2 and numbers >= 2:
            score += 30
        elif letters >= 1 and numbers >= 1:  # More lenient
            score += 15
        elif letters + numbers >= 4:  # Very lenient
            score += 5

        # Pattern matching
        for pattern in self.plate_patterns.values():
            if re.match(pattern, text):
                score += 15
                break

        # STATE-CODE BONUS: Extra points for valid state codes
        if self.has_valid_state_code(text):
            score += 25
            logging.info(f"State code bonus applied for: {text[:2]}")

        # Confidence bonus
        conf_bonus = (confidence / 100) * 20
        score += conf_bonus

        # Reduced penalties
        if re.search(r'(.)\1{3,}', clean_text):
            score -= 3  # Reduced from 5
        if len(clean_text) > 15:
            score -= 5  # Reduced from 8

        return max(0, score)

    def process_plate(self, plate_img, detection_id, output_dir):
        """Process a single license plate image with aggressive OCR"""
        logging.info(f"Aggressive OCR processing plate {detection_id}...")
        
        # Use super resolution enhancement
        img_variants = self.preprocess_plate_image(plate_img)

        # Save debug images
        for variant_name, variant_img in img_variants.items():
            debug_path = os.path.join(output_dir, f"plate_{detection_id}_{variant_name}.jpg")
            try:
                cv2.imwrite(debug_path, variant_img)
            except Exception as e:
                logging.warning(f"Failed to save debug image {debug_path}: {e}")

        # Run both standard and aggressive OCR
        all_results = []
        all_results.extend(self.tesseract_ocr(img_variants))  # Standard with relaxed filtering
        all_results.extend(self.easyocr_ocr(img_variants))    # Standard with relaxed filtering
        all_results.extend(self.aggressive_tesseract_ocr(img_variants))  # Aggressive
        all_results.extend(self.aggressive_easyocr(img_variants))        # Aggressive

        # If no results, use fallback
        if not all_results:
            logging.info("No results found, using fallback OCR")
            all_results = self.fallback_ocr_without_state_filtering(img_variants)

        scored_results = []
        seen_texts = set()
        
        for result in all_results:
            cleaned_text = result.get('cleaned_text', self.clean_and_format_text(result['text'], result['confidence']))
            if cleaned_text and cleaned_text not in seen_texts:
                seen_texts.add(cleaned_text)
                score = self.score_license_plate(cleaned_text, result['confidence'])

                scored_results.append({
                    'text': cleaned_text,
                    'score': score,
                    'engine': result['engine'],
                    'variant': result['variant'],
                    'config': result['config'],
                    'confidence': result['confidence'],
                    'lines': result.get('lines', 1),
                    'valid_state': result.get('valid_state', False)
                })

        # Log all results for debugging
        logging.info(f"Found {len(scored_results)} OCR results:")
        for i, result in enumerate(scored_results[:10]):  # Top 10
            state_status = " [VALID STATE]" if result['valid_state'] else ""
            logging.info(f"  {i+1}. {result['engine']}: '{result['text']}' (score: {result['score']:.1f}, conf: {result['confidence']:.1f}{state_status})")

        if scored_results:
            scored_results.sort(key=lambda x: x['score'], reverse=True)
            best_result = scored_results[0]
            state_status = " [VALID STATE]" if best_result['valid_state'] else " [NO STATE VALIDATION]"
            logging.info(f"Best result: '{best_result['text']}' (Score: {best_result['score']:.2f}, Engine: {best_result['engine']}{state_status})")
            return best_result['text'], best_result['score']
        
        logging.warning("No valid OCR results found.")
        return "UNREADABLE", 0

    def fallback_ocr_without_state_filtering(self, img_variants):
        """Fallback OCR without any state filtering"""
        results = []
        
        # Very lenient Tesseract fallback
        configs = [
            {'psm': 7, 'oem': 3},
            {'psm': 8, 'oem': 3},
            {'psm': 13, 'oem': 3},
        ]
        
        for variant_name, img in img_variants.items():
            for config in configs:
                try:
                    custom_config = f"--oem {config['oem']} --psm {config['psm']}"
                    data = pytesseract.image_to_data(img, config=custom_config, output_type=pytesseract.Output.DICT)
                    
                    # Extract any text with any confidence
                    text_items = []
                    conf_items = []
                    
                    for i in range(len(data['text'])):
                        text = data['text'][i].strip()
                        conf = int(data['conf'][i])
                        if text:
                            text_items.append(text)
                            conf_items.append(max(conf, 1))  # Minimum confidence 1
                    
                    if text_items:
                        combined_text = ' '.join(text_items)
                        avg_conf = np.mean(conf_items) if conf_items else 1

                        if len(combined_text.replace(' ', '')) >= 3:  # Very lenient
                            cleaned_text = self.clean_and_format_text(combined_text, avg_conf)
                            results.append({
                                'engine': 'tesseract_fallback',
                                'variant': variant_name,
                                'config': f"psm{config['psm']}",
                                'text': combined_text,
                                'cleaned_text': cleaned_text,
                                'confidence': avg_conf,
                                'lines': len(text_items),
                                'valid_state': False
                            })
                except Exception as e:
                    continue

        # EasyOCR fallback
        if self.easyocr_reader:
            for variant_name, img in img_variants.items():
                try:
                    ocr_result = self.easyocr_reader.readtext(
                        img,
                        allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                        width_ths=0.1, height_ths=0.1, text_threshold=0.1
                    )
                    
                    if ocr_result:
                        all_text = ' '.join([result[1] for result in ocr_result if result[1].strip()])
                        confidences = [result[2] for result in ocr_result if result[1].strip()]
                        avg_conf = np.mean(confidences) if confidences else 0.1
                        
                        if all_text and len(all_text.replace(' ', '')) >= 3:
                            cleaned_text = self.clean_and_format_text(all_text, avg_conf * 100)
                            results.append({
                                'engine': 'easyocr_fallback',
                                'variant': variant_name,
                                'config': 'fallback_params',
                                'text': all_text,
                                'cleaned_text': cleaned_text,
                                'confidence': avg_conf * 100,
                                'lines': len(ocr_result),
                                'valid_state': False
                            })
                except Exception as e:
                    continue

        return results