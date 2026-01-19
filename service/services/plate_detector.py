"""
Plate Detector Service
High-level detection service with caching and deduplication
"""
import asyncio
import time
from typing import Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

from config import settings
from models.detector import detect_plate_in_frame, DetectionResult


@dataclass
class DetectionEvent:
    """Represents a plate detection event"""
    plate_text: str
    confidence: float
    camera_id: str
    camera_type: str  # 'entry' or 'exit'
    timestamp: float
    plate_bbox: Optional[tuple] = None
    vehicle_bbox: Optional[tuple] = None
    vehicle_class: Optional[str] = None


class PlateDetectorService:
    """
    Service for detecting license plates with deduplication.
    Prevents duplicate detections of the same plate within cooldown period.
    """

    def __init__(self):
        self._last_detections: dict[str, float] = {}  # plate -> timestamp
        self._detection_callbacks: list[Callable[[DetectionEvent], None]] = []
        self._cooldown = settings.DETECTION_COOLDOWN

    def add_detection_callback(self, callback: Callable[[DetectionEvent], None]):
        """Register a callback for detection events"""
        self._detection_callbacks.append(callback)

    def remove_detection_callback(self, callback: Callable[[DetectionEvent], None]):
        """Remove a registered callback"""
        if callback in self._detection_callbacks:
            self._detection_callbacks.remove(callback)

    def _is_duplicate(self, plate_text: str) -> bool:
        """Check if this plate was recently detected"""
        if plate_text in self._last_detections:
            last_time = self._last_detections[plate_text]
            if time.time() - last_time < self._cooldown:
                return True
        return False

    def _record_detection(self, plate_text: str):
        """Record detection timestamp for deduplication"""
        self._last_detections[plate_text] = time.time()

        # Cleanup old entries
        current_time = time.time()
        self._last_detections = {
            plate: ts
            for plate, ts in self._last_detections.items()
            if current_time - ts < self._cooldown * 10
        }

    async def _notify_callbacks(self, event: DetectionEvent):
        """Notify all registered callbacks of a detection"""
        for callback in self._detection_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                print(f"Error in detection callback: {e}")

    async def process_frame(
        self,
        frame: np.ndarray,
        camera_id: str,
        camera_type: str = "entry"
    ) -> tuple[DetectionResult, Optional[DetectionEvent]]:
        """
        Process a single frame for plate detection.

        Returns:
            tuple: (DetectionResult, DetectionEvent or None if duplicate)
        """
        # Run detection
        result = detect_plate_in_frame(frame, settings.MIN_CONFIDENCE)

        event = None

        if result.plate_text:
            # Check for duplicate
            if not self._is_duplicate(result.plate_text):
                # New detection!
                self._record_detection(result.plate_text)

                event = DetectionEvent(
                    plate_text=result.plate_text,
                    confidence=result.plate_confidence,
                    camera_id=camera_id,
                    camera_type=camera_type,
                    timestamp=time.time(),
                    plate_bbox=result.plate_bbox,
                    vehicle_bbox=result.vehicle_bbox,
                    vehicle_class=result.vehicle_class
                )

                # Notify callbacks
                await self._notify_callbacks(event)

        return result, event

    def clear_history(self):
        """Clear detection history"""
        self._last_detections.clear()


# Singleton instance
plate_detector_service = PlateDetectorService()
