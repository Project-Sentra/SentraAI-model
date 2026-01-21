"""
Camera Manager Service
Handles camera streams and frame distribution
"""
import asyncio
import cv2
import base64
import time
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

from config import settings
from services.plate_detector import plate_detector_service, DetectionEvent
from services.parking_client import parking_client


class CameraType(Enum):
    ENTRY = "entry"
    EXIT = "exit"


class CameraStatus(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"


@dataclass
class Camera:
    """Represents a camera source"""
    id: str
    name: str
    camera_type: CameraType
    source: str
    status: CameraStatus = CameraStatus.STOPPED
    last_frame: Optional[np.ndarray] = None
    last_detection: Optional[DetectionEvent] = None
    frame_count: int = 0
    error_message: Optional[str] = None


@dataclass
class FrameUpdate:
    """Frame update for WebSocket broadcast"""
    camera_id: str
    frame_base64: str
    timestamp: float
    detection: Optional[dict] = None


class CameraManager:
    """Manages camera streams and broadcasts frames via WebSocket"""

    def __init__(self):
        self._cameras: dict[str, Camera] = {}
        self._capture_tasks: dict[str, asyncio.Task] = {}
        self._frame_callbacks: list[Callable[[FrameUpdate], Any]] = []
        self._detection_callbacks: list[Callable[[DetectionEvent, Any], Any]] = []
        self._running = False

    async def initialize(self):
        """Initialize cameras based on configuration"""
        self._running = True

        # Setup entry camera
        entry_camera = Camera(
            id="entry_cam_01",
            name="Entry Gate 01",
            camera_type=CameraType.ENTRY,
            source=settings.ENTRY_CAMERA_SOURCE
        )
        self._cameras[entry_camera.id] = entry_camera

        # Setup exit camera
        exit_camera = Camera(
            id="exit_cam_01",
            name="Exit Gate 01",
            camera_type=CameraType.EXIT,
            source=settings.EXIT_CAMERA_SOURCE
        )
        self._cameras[exit_camera.id] = exit_camera

        # Register detection callback
        plate_detector_service.add_detection_callback(self._on_detection)

        print(f"Initialized {len(self._cameras)} cameras")

    async def cleanup(self):
        """Cleanup resources"""
        self._running = False

        # Stop all capture tasks
        for camera_id in list(self._capture_tasks.keys()):
            await self.stop_camera(camera_id)

        # Close parking client
        await parking_client.close()

    def add_frame_callback(self, callback: Callable[[FrameUpdate], Any]):
        """Register a callback for frame updates"""
        self._frame_callbacks.append(callback)

    def remove_frame_callback(self, callback: Callable[[FrameUpdate], Any]):
        """Remove a frame callback"""
        if callback in self._frame_callbacks:
            self._frame_callbacks.remove(callback)

    def add_detection_callback(self, callback: Callable[[DetectionEvent, Any], Any]):
        """Register a callback for detection events"""
        self._detection_callbacks.append(callback)

    async def _on_detection(self, event: DetectionEvent):
        """Handle detection event from plate detector"""
        camera = self._cameras.get(event.camera_id)
        if camera:
            camera.last_detection = event

        # Handle auto entry/exit if enabled
        if settings.AUTO_ENTRY_EXIT:
            await self._handle_auto_action(event)

        # Notify callbacks
        for callback in self._detection_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event, None)
                else:
                    callback(event, None)
            except Exception as e:
                print(f"Error in detection callback: {e}")

    async def _handle_auto_action(self, event: DetectionEvent):
        """Automatically process entry/exit based on camera type"""
        if event.camera_type == "entry":
            result = await parking_client.vehicle_entry(event.plate_text)
            print(f"Auto entry for {event.plate_text}: {result.message}")
        elif event.camera_type == "exit":
            result = await parking_client.vehicle_exit(event.plate_text)
            print(f"Auto exit for {event.plate_text}: {result.message}")

    def get_cameras(self) -> list[dict]:
        """Get list of all cameras"""
        return [
            {
                "id": cam.id,
                "name": cam.name,
                "type": cam.camera_type.value,
                "status": cam.status.value,
                "source": cam.source,
                "frame_count": cam.frame_count,
                "error": cam.error_message
            }
            for cam in self._cameras.values()
        ]

    def get_camera(self, camera_id: str) -> Optional[Camera]:
        """Get camera by ID"""
        return self._cameras.get(camera_id)

    def get_active_count(self) -> int:
        """Get count of active cameras"""
        return sum(
            1 for cam in self._cameras.values()
            if cam.status == CameraStatus.RUNNING
        )

    async def start_camera(self, camera_id: str) -> bool:
        """Start streaming from a camera"""
        camera = self._cameras.get(camera_id)
        if not camera:
            return False

        if camera_id in self._capture_tasks:
            return True  # Already running

        # Start capture task
        task = asyncio.create_task(self._capture_loop(camera))
        self._capture_tasks[camera_id] = task

        return True

    async def stop_camera(self, camera_id: str) -> bool:
        """Stop streaming from a camera"""
        if camera_id not in self._capture_tasks:
            return False

        task = self._capture_tasks.pop(camera_id)
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        camera = self._cameras.get(camera_id)
        if camera:
            camera.status = CameraStatus.STOPPED

        return True

    async def _capture_loop(self, camera: Camera):
        """Main capture loop for a camera"""
        cap = None
        frame_skip = settings.FRAME_SKIP

        try:
            # Open video source
            if camera.source.isdigit():
                cap = cv2.VideoCapture(int(camera.source))
            else:
                cap = cv2.VideoCapture(camera.source)

            if not cap.isOpened():
                camera.status = CameraStatus.ERROR
                camera.error_message = f"Failed to open video source: {camera.source}"
                print(f"[CRITICAL] Failed to open video source: {camera.source}")
                return

            print(f"[INFO] Successfully opened video source: {camera.source}")
            camera.status = CameraStatus.RUNNING
            camera.error_message = None
            frame_count = 0

            while self._running:
                ret, frame = cap.read()

                if not ret:
                    # Loop video for simulated mode
                    if settings.CAMERA_MODE == "simulated":
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        break

                frame_count += 1
                camera.frame_count = frame_count

                # Skip frames for performance
                if frame_count % frame_skip != 0:
                    await asyncio.sleep(0.01)
                    continue

                # Resize frame
                frame = cv2.resize(
                    frame,
                    (settings.FRAME_WIDTH, settings.FRAME_HEIGHT)
                )

                # Process frame for plate detection
                result, detection = await plate_detector_service.process_frame(
                    frame,
                    camera.id,
                    camera.camera_type.value
                )

                # Use frame with overlay if available
                display_frame = result.frame_with_overlay if result.frame_with_overlay is not None else frame
                camera.last_frame = display_frame

                # Encode frame as JPEG base64
                _, buffer = cv2.imencode(
                    '.jpg',
                    display_frame,
                    [cv2.IMWRITE_JPEG_QUALITY, settings.JPEG_QUALITY]
                )
                frame_base64 = base64.b64encode(buffer).decode('utf-8')

                # Create frame update
                update = FrameUpdate(
                    camera_id=camera.id,
                    frame_base64=frame_base64,
                    timestamp=time.time(),
                    detection=detection.plate_text if detection else None
                )

                # Broadcast to callbacks
                await self._broadcast_frame(update)

                # Control frame rate
                await asyncio.sleep(1/30)  # ~30 FPS

        except asyncio.CancelledError:
            pass
        except Exception as e:
            camera.status = CameraStatus.ERROR
            camera.error_message = str(e)
            print(f"Camera {camera.id} error: {e}")
        finally:
            if cap:
                cap.release()
            camera.status = CameraStatus.STOPPED

    async def _broadcast_frame(self, update: FrameUpdate):
        """Broadcast frame update to all callbacks"""
        for callback in self._frame_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(update)
                else:
                    callback(update)
            except Exception as e:
                print(f"Error in frame callback: {e}")


# Singleton instance
camera_manager = CameraManager()
