# test_license_plate_ocr.py
import cv2
import os
import sys
import argparse
from datetime import datetime

# Add the path to your OCR modules
sys.path.append(os.path.dirname(__file__))

from saferide_backend.saferide_backend.license_plate_ocr import LicensePlateOCR

def test_license_plate_ocr(image_path, output_dir=None):
    """
    Test the license plate OCR on a single cropped license plate image
    """
    # Create output directory for debug images
    if output_dir is None:
        output_dir = "ocr_test_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize the OCR processor
    print("Initializing License Plate OCR...")
    lp_ocr = LicensePlateOCR()
    print("OCR initialized successfully!")
    
    # Load the image
    print(f"\nLoading image: {image_path}")
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image from {image_path}")
        return
    
    print(f"Image loaded - Shape: {image.shape}")
    
    # Generate a unique detection ID
    detection_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Process the license plate
    print(f"\nProcessing license plate with detection ID: {detection_id}")
    print("Running OCR...")
    
    license_plate_text, ocr_score = lp_ocr.process_plate(
        image, 
        detection_id=detection_id,
        output_dir=output_dir
    )
    
    # Display results
    print("\n" + "="*50)
    print("OCR RESULTS")
    print("="*50)
    print(f"Detected Text: '{license_plate_text}'")
    print(f"OCR Score: {ocr_score:.2f}")
    print(f"Debug images saved to: {output_dir}")
    print("="*50)
    
    # Save the original image with results in filename for easy reference
    result_filename = f"result_{detection_id}_{license_plate_text}_{ocr_score:.0f}.jpg"
    result_path = os.path.join(output_dir, result_filename)
    cv2.imwrite(result_path, image)
    print(f"Result saved as: {result_filename}")
    
    return license_plate_text, ocr_score

def batch_test_ocr(image_folder, output_dir=None):
    """
    Test OCR on multiple images in a folder
    """
    if output_dir is None:
        output_dir = "batch_ocr_test_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize OCR
    print("Initializing License Plate OCR...")
    lp_ocr = LicensePlateOCR()
    
    # Get all image files
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    image_files = [f for f in os.listdir(image_folder) 
                  if f.lower().endswith(image_extensions)]
    
    if not image_files:
        print(f"No image files found in {image_folder}")
        return
    
    print(f"Found {len(image_files)} images to process")
    
    results = []
    
    for i, image_file in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}] Processing: {image_file}")
        
        image_path = os.path.join(image_folder, image_file)
        image = cv2.imread(image_path)
        
        if image is None:
            print(f"  Error loading image: {image_file}")
            continue
        
        detection_id = f"batch_{i}_{os.path.splitext(image_file)[0]}"
        
        try:
            license_plate_text, ocr_score = lp_ocr.process_plate(
                image, 
                detection_id=detection_id,
                output_dir=output_dir
            )
            
            result = {
                'filename': image_file,
                'detected_text': license_plate_text,
                'ocr_score': ocr_score,
                'success': license_plate_text != "UNREADABLE"
            }
            results.append(result)
            
            print(f"  Result: '{license_plate_text}' (Score: {ocr_score:.2f})")
            
        except Exception as e:
            print(f"  Error processing {image_file}: {e}")
            results.append({
                'filename': image_file,
                'detected_text': "ERROR",
                'ocr_score': 0,
                'success': False,
                'error': str(e)
            })
    
    # Print summary
    print("\n" + "="*60)
    print("BATCH PROCESSING SUMMARY")
    print("="*60)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"Total images processed: {len(results)}")
    print(f"Successful OCR: {len(successful)}")
    print(f"Failed OCR: {len(failed)}")
    print(f"Success rate: {len(successful)/len(results)*100:.1f}%")
    
    if successful:
        print("\nSuccessful detections:")
        for result in successful:
            print(f"  {result['filename']}: '{result['detected_text']}' (Score: {result['ocr_score']:.2f})")
    
    if failed:
        print("\nFailed detections:")
        for result in failed:
            error_msg = result.get('error', 'UNREADABLE')
            print(f"  {result['filename']}: {error_msg}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Test License Plate OCR')
    parser.add_argument('--image', '-i', help='Path to single license plate image')
    parser.add_argument('--folder', '-f', help='Path to folder containing license plate images')
    parser.add_argument('--output', '-o', default='ocr_test_results', 
                       help='Output directory for results (default: ocr_test_results)')
    
    args = parser.parse_args()
    
    if args.image:
        # Single image test
        test_license_plate_ocr(args.image, args.output)
    
    elif args.folder:
        # Batch test
        batch_test_ocr(args.folder, args.output)
    
    else:
        print("Please specify either --image for single image or --folder for batch processing")
        print("Examples:")
        print("  python test_license_plate_ocr.py --image plate1.jpg")
        print("  python test_license_plate_ocr.py --folder ./test_plates/")
        print("  python test_license_plate_ocr.py --image plate1.jpg --output my_results")

if __name__ == "__main__":
    main()