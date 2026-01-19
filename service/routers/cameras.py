"""
Camera Router
Handles camera management and WebSocket streaming
"""
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import Optional

from services.camera_manager import camera_manager, FrameUpdate
from services.plate_detector import DetectionEvent
from services.parking_client import parking_client
from config import settings


router = APIRouter()


class CameraResponse(BaseModel):
    """Response model for camera info"""
    id: str
    name: str
    type: str
    status: str
    source: str
    frame_count: int
    error: Optional[str] = None


class ActionRequest(BaseModel):
    """Request model for entry/exit actions"""
    plate_number: str
    camera_id: str


class ActionResponse(BaseModel):
    """Response model for entry/exit actions"""
    success: bool
    message: str
    spot_name: Optional[str] = None
    duration_minutes: Optional[int] = None
    amount_charged: Optional[int] = None


@router.get("/cameras")
async def list_cameras() -> list[CameraResponse]:
    """Get list of all configured cameras"""
    cameras = camera_manager.get_cameras()
    return [CameraResponse(**cam) for cam in cameras]


@router.get("/cameras/{camera_id}")
async def get_camera(camera_id: str) -> CameraResponse:
    """Get details of a specific camera"""
    camera = camera_manager.get_camera(camera_id)
    if not camera:
        raise HTTPException(404, f"Camera {camera_id} not found")

    return CameraResponse(
        id=camera.id,
        name=camera.name,
        type=camera.camera_type.value,
        status=camera.status.value,
        source=camera.source,
        frame_count=camera.frame_count,
        error=camera.error_message
    )


@router.post("/cameras/{camera_id}/start")
async def start_camera(camera_id: str):
    """Start streaming from a camera"""
    camera = camera_manager.get_camera(camera_id)
    if not camera:
        raise HTTPException(404, f"Camera {camera_id} not found")

    success = await camera_manager.start_camera(camera_id)

    if success:
        return {"message": f"Camera {camera_id} started", "status": "running"}
    else:
        raise HTTPException(500, f"Failed to start camera {camera_id}")


@router.post("/cameras/{camera_id}/stop")
async def stop_camera(camera_id: str):
    """Stop streaming from a camera"""
    success = await camera_manager.stop_camera(camera_id)

    if success:
        return {"message": f"Camera {camera_id} stopped", "status": "stopped"}
    else:
        raise HTTPException(404, f"Camera {camera_id} not found or not running")


@router.post("/cameras/start-all")
async def start_all_cameras():
    """Start all configured cameras"""
    cameras = camera_manager.get_cameras()
    started = []

    for cam in cameras:
        if await camera_manager.start_camera(cam["id"]):
            started.append(cam["id"])

    return {
        "message": f"Started {len(started)} cameras",
        "cameras": started
    }


@router.post("/cameras/stop-all")
async def stop_all_cameras():
    """Stop all running cameras"""
    cameras = camera_manager.get_cameras()
    stopped = []

    for cam in cameras:
        if await camera_manager.stop_camera(cam["id"]):
            stopped.append(cam["id"])

    return {
        "message": f"Stopped {len(stopped)} cameras",
        "cameras": stopped
    }


@router.post("/entry", response_model=ActionResponse)
async def confirm_entry(request: ActionRequest):
    """Confirm vehicle entry (manual confirmation mode)"""
    result = await parking_client.vehicle_entry(request.plate_number)

    return ActionResponse(
        success=result.success,
        message=result.message,
        spot_name=result.spot_name
    )


@router.post("/exit", response_model=ActionResponse)
async def confirm_exit(request: ActionRequest):
    """Confirm vehicle exit (manual confirmation mode)"""
    result = await parking_client.vehicle_exit(request.plate_number)

    return ActionResponse(
        success=result.success,
        message=result.message,
        duration_minutes=result.duration_minutes,
        amount_charged=result.amount_charged
    )


# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        # Cleanup disconnected
        for conn in disconnected:
            self.disconnect(conn)


ws_manager = ConnectionManager()


# Frame callback for WebSocket broadcasting
async def broadcast_frame(update: FrameUpdate):
    """Broadcast frame update to WebSocket clients"""
    message = {
        "type": "frame_update",
        "camera_id": update.camera_id,
        "frame": update.frame_base64,
        "timestamp": update.timestamp,
        "detection": update.detection
    }
    await ws_manager.broadcast(message)


# Detection callback for WebSocket broadcasting
async def broadcast_detection(event: DetectionEvent, _):
    """Broadcast detection event to WebSocket clients"""
    message = {
        "type": "plate_detected",
        "camera_id": event.camera_id,
        "camera_type": event.camera_type,
        "plate_text": event.plate_text,
        "confidence": event.confidence,
        "timestamp": event.timestamp,
        "plate_bbox": event.plate_bbox,
        "vehicle_bbox": event.vehicle_bbox,
        "vehicle_class": event.vehicle_class
    }
    await ws_manager.broadcast(message)


# Register callbacks
camera_manager.add_frame_callback(broadcast_frame)
camera_manager.add_detection_callback(broadcast_detection)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time camera feeds and detection events.

    Events sent to clients:
    - frame_update: Contains camera_id, base64 frame, and optional detection
    - plate_detected: Contains detection details
    - entry_result: Result of entry action
    - exit_result: Result of exit action

    Commands from clients:
    - {"action": "start_camera", "camera_id": "..."}
    - {"action": "stop_camera", "camera_id": "..."}
    - {"action": "confirm_entry", "plate_number": "...", "camera_id": "..."}
    - {"action": "confirm_exit", "plate_number": "...", "camera_id": "..."}
    """
    await ws_manager.connect(websocket)

    try:
        # Send initial camera list
        cameras = camera_manager.get_cameras()
        await websocket.send_json({
            "type": "cameras_list",
            "cameras": cameras
        })

        # Listen for commands
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "start_camera":
                camera_id = data.get("camera_id")
                success = await camera_manager.start_camera(camera_id)
                await websocket.send_json({
                    "type": "camera_status",
                    "camera_id": camera_id,
                    "status": "running" if success else "error"
                })

            elif action == "stop_camera":
                camera_id = data.get("camera_id")
                success = await camera_manager.stop_camera(camera_id)
                await websocket.send_json({
                    "type": "camera_status",
                    "camera_id": camera_id,
                    "status": "stopped" if success else "error"
                })

            elif action == "confirm_entry":
                plate_number = data.get("plate_number")
                camera_id = data.get("camera_id")
                result = await parking_client.vehicle_entry(plate_number)
                await websocket.send_json({
                    "type": "entry_result",
                    "success": result.success,
                    "message": result.message,
                    "spot_name": result.spot_name,
                    "plate_number": plate_number
                })

            elif action == "confirm_exit":
                plate_number = data.get("plate_number")
                camera_id = data.get("camera_id")
                result = await parking_client.vehicle_exit(plate_number)
                await websocket.send_json({
                    "type": "exit_result",
                    "success": result.success,
                    "message": result.message,
                    "duration_minutes": result.duration_minutes,
                    "amount_charged": result.amount_charged,
                    "plate_number": plate_number
                })

            elif action == "start_all":
                cameras = camera_manager.get_cameras()
                for cam in cameras:
                    await camera_manager.start_camera(cam["id"])
                await websocket.send_json({
                    "type": "all_cameras_started"
                })

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)
