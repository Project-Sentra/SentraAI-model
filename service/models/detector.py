"""
YOLO + EasyOCR Detection Wrapper
Combines vehicle detection, plate detection, and OCR
"""
import cv2
import numpy as np
from typing import Optional
import easyocr
from pathlib import Path

# Lazy loading for models
_yolo_model = None
_plate_model = None
_ocr_reader = None


def get_yolo_model():
    """Lazy load YOLOv8 model for vehicle detection"""
    global _yolo_model
    if _yolo_model is None:
        from ultralytics import YOLO
        from config import settings

        # Check if custom model exists, otherwise use pretrained
        model_path = Path(settings.YOLO_MODEL)
        if model_path.exists():
            _yolo_model = YOLO(str(model_path))
        else:
            print(f"Custom YOLO model not found at {model_path}, using pretrained yolov8n.pt")
            _yolo_model = YOLO('yolov8n.pt')

    return _yolo_model


def get_plate_model():
    """Lazy load custom plate detector model"""
    global _plate_model
    if _plate_model is None:
        from ultralytics import YOLO
        from config import settings

        model_path = Path(settings.PLATE_DETECTOR_MODEL)
        if model_path.exists():
            _plate_model = YOLO(str(model_path))
        else:
            print(f"Plate detector model not found at {model_path}")
            _plate_model = None

    return _plate_model


def get_ocr_reader():
    """Lazy load EasyOCR reader"""
    global _ocr_reader
    if _ocr_reader is None:
        _ocr_reader = easyocr.Reader(['en'], gpu=False)
    return _ocr_reader


# Vehicle class IDs in COCO dataset
VEHICLE_CLASS_IDS = [2, 3, 5, 7]  # car, motorcycle, bus, truck


class DetectionResult:
    """Container for detection results"""
    def __init__(
        self,
        plate_text: Optional[str] = None,
        plate_confidence: float = 0.0,
        plate_bbox: Optional[tuple] = None,
        vehicle_bbox: Optional[tuple] = None,
        vehicle_class: Optional[str] = None,
        frame_with_overlay: Optional[np.ndarray] = None
    ):
        self.plate_text = plate_text
        self.plate_confidence = plate_confidence
        self.plate_bbox = plate_bbox
        self.vehicle_bbox = vehicle_bbox
        self.vehicle_class = vehicle_class
        self.frame_with_overlay = frame_with_overlay

    def to_dict(self) -> dict:
        return {
            "plate_text": self.plate_text,
            "plate_confidence": self.plate_confidence,
            "plate_bbox": self.plate_bbox,
            "vehicle_bbox": self.vehicle_bbox,
            "vehicle_class": self.vehicle_class,
        }


def preprocess_plate_image(plate_crop: np.ndarray) -> np.ndarray:
    """Preprocess plate crop for better OCR"""
    # Convert to grayscale
    gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)

    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11, 2
    )

    # Denoise
    denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)

    return denoised


def read_plate_text(plate_crop: np.ndarray) -> tuple[Optional[str], float]:
    """Read text from plate crop using EasyOCR"""
    from utils.sri_lankan_plates import smart_format_plate

    reader = get_ocr_reader()

    # Try with original image
    results = reader.readtext(plate_crop)

    best_text = None
    best_confidence = 0.0

    for detection in results:
        text = detection[1].upper().replace(' ', '')
        confidence = detection[2]

        # Try to format as Sri Lankan plate
        formatted, format_confidence = smart_format_plate(text)

        if formatted and (confidence * format_confidence) > best_confidence:
            best_text = formatted
            best_confidence = confidence * format_confidence

    # If no good result, try with preprocessed image
    if best_confidence < 0.5:
        preprocessed = preprocess_plate_image(plate_crop)
        results = reader.readtext(preprocessed)

        for detection in results:
            text = detection[1].upper().replace(' ', '')
            confidence = detection[2]

            formatted, format_confidence = smart_format_plate(text)

            if formatted and (confidence * format_confidence) > best_confidence:
                best_text = formatted
                best_confidence = confidence * format_confidence

    return best_text, best_confidence


def detect_vehicles(frame: np.ndarray) -> list[dict]:
    """Detect vehicles in frame"""
    yolo = get_yolo_model()
    results = yolo(frame, verbose=False)[0]

    vehicles = []
    for detection in results.boxes.data.tolist():
        x1, y1, x2, y2, conf, class_id = detection

        if int(class_id) in VEHICLE_CLASS_IDS:
            vehicles.append({
                'bbox': (int(x1), int(y1), int(x2), int(y2)),
                'confidence': conf,
                'class_id': int(class_id),
                'class_name': results.names[int(class_id)]
            })

    return vehicles


def detect_plates(frame: np.ndarray) -> list[dict]:
    """Detect license plates in frame"""
    plate_model = get_plate_model()

    if plate_model is None:
        return []

    results = plate_model(frame, verbose=False)[0]

    plates = []
    for detection in results.boxes.data.tolist():
        x1, y1, x2, y2, conf, class_id = detection
        plates.append({
            'bbox': (int(x1), int(y1), int(x2), int(y2)),
            'confidence': conf
        })

    return plates


def draw_detection_overlay(
    frame: np.ndarray,
    plate_bbox: Optional[tuple] = None,
    plate_text: Optional[str] = None,
    vehicle_bbox: Optional[tuple] = None
) -> np.ndarray:
    """Draw bounding boxes and labels on frame"""
    overlay = frame.copy()

    # Draw vehicle bbox in blue
    if vehicle_bbox:
        x1, y1, x2, y2 = vehicle_bbox
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (255, 128, 0), 2)

    # Draw plate bbox in green
    if plate_bbox:
        x1, y1, x2, y2 = plate_bbox
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Draw plate text above bbox
        if plate_text:
            # Background for text
            text_size = cv2.getTextSize(plate_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
            cv2.rectangle(
                overlay,
                (x1, y1 - text_size[1] - 10),
                (x1 + text_size[0] + 10, y1),
                (0, 255, 0),
                -1
            )
            cv2.putText(
                overlay,
                plate_text,
                (x1 + 5, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 0),
                2
            )

    return overlay


def detect_plate_in_frame(frame: np.ndarray, min_confidence: float = 0.6) -> DetectionResult:
    """
    Main detection pipeline for a single frame.
    Detects vehicles, license plates, and reads plate text.
    """
    result = DetectionResult()

    # Detect vehicles
    vehicles = detect_vehicles(frame)

    # Detect plates
    plates = detect_plates(frame)

    if not plates:
        result.frame_with_overlay = frame
        return result

    # Find best plate detection
    best_plate = max(plates, key=lambda p: p['confidence'])

    if best_plate['confidence'] < min_confidence:
        result.frame_with_overlay = frame
        return result

    # Extract plate region
    x1, y1, x2, y2 = best_plate['bbox']
    plate_crop = frame[y1:y2, x1:x2]

    if plate_crop.size == 0:
        result.frame_with_overlay = frame
        return result

    # Read plate text
    plate_text, text_confidence = read_plate_text(plate_crop)

    # Find associated vehicle
    vehicle_bbox = None
    vehicle_class = None

    for vehicle in vehicles:
        vx1, vy1, vx2, vy2 = vehicle['bbox']
        # Check if plate is inside vehicle bbox
        if x1 >= vx1 and y1 >= vy1 and x2 <= vx2 and y2 <= vy2:
            vehicle_bbox = vehicle['bbox']
            vehicle_class = vehicle['class_name']
            break

    # Build result
    if plate_text and text_confidence >= min_confidence:
        result.plate_text = plate_text
        result.plate_confidence = text_confidence
        result.plate_bbox = best_plate['bbox']
        result.vehicle_bbox = vehicle_bbox
        result.vehicle_class = vehicle_class

    # Draw overlay
    result.frame_with_overlay = draw_detection_overlay(
        frame,
        plate_bbox=best_plate['bbox'] if result.plate_text else None,
        plate_text=result.plate_text,
        vehicle_bbox=vehicle_bbox
    )

    return result
