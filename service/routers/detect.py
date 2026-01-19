"""
Detection Router
Handles image-based plate detection requests
"""
import cv2
import numpy as np
import base64
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional

from models.detector import detect_plate_in_frame
from config import settings


router = APIRouter()


class DetectionResponse(BaseModel):
    """Response model for detection endpoint"""
    success: bool
    plate_text: Optional[str] = None
    confidence: Optional[float] = None
    plate_bbox: Optional[list] = None
    vehicle_bbox: Optional[list] = None
    vehicle_class: Optional[str] = None
    message: Optional[str] = None
    processed_image: Optional[str] = None  # Base64 encoded


class Base64ImageRequest(BaseModel):
    """Request model for base64 image detection"""
    image: str  # Base64 encoded image
    return_image: bool = False


@router.post("/detect/image", response_model=DetectionResponse)
async def detect_from_upload(
    file: UploadFile = File(...),
    return_image: bool = False
):
    """
    Detect license plate from uploaded image file.

    - **file**: Image file (JPEG, PNG)
    - **return_image**: If true, return processed image with overlays
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")

    try:
        # Read image data
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(400, "Could not decode image")

        # Run detection
        result = detect_plate_in_frame(frame, settings.MIN_CONFIDENCE)

        response = DetectionResponse(
            success=result.plate_text is not None,
            plate_text=result.plate_text,
            confidence=result.plate_confidence if result.plate_text else None,
            plate_bbox=list(result.plate_bbox) if result.plate_bbox else None,
            vehicle_bbox=list(result.vehicle_bbox) if result.vehicle_bbox else None,
            vehicle_class=result.vehicle_class,
            message="Plate detected" if result.plate_text else "No plate detected"
        )

        # Include processed image if requested
        if return_image and result.frame_with_overlay is not None:
            _, buffer = cv2.imencode('.jpg', result.frame_with_overlay)
            response.processed_image = base64.b64encode(buffer).decode('utf-8')

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Detection failed: {str(e)}")


@router.post("/detect/base64", response_model=DetectionResponse)
async def detect_from_base64(request: Base64ImageRequest):
    """
    Detect license plate from base64 encoded image.

    - **image**: Base64 encoded image data
    - **return_image**: If true, return processed image with overlays
    """
    try:
        # Decode base64 image
        image_data = base64.b64decode(request.image)
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(400, "Could not decode image")

        # Run detection
        result = detect_plate_in_frame(frame, settings.MIN_CONFIDENCE)

        response = DetectionResponse(
            success=result.plate_text is not None,
            plate_text=result.plate_text,
            confidence=result.plate_confidence if result.plate_text else None,
            plate_bbox=list(result.plate_bbox) if result.plate_bbox else None,
            vehicle_bbox=list(result.vehicle_bbox) if result.vehicle_bbox else None,
            vehicle_class=result.vehicle_class,
            message="Plate detected" if result.plate_text else "No plate detected"
        )

        # Include processed image if requested
        if request.return_image and result.frame_with_overlay is not None:
            _, buffer = cv2.imencode('.jpg', result.frame_with_overlay)
            response.processed_image = base64.b64encode(buffer).decode('utf-8')

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Detection failed: {str(e)}")
