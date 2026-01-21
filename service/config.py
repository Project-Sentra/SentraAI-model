"""
SentraAI Service Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / "models"
SAMPLE_VIDEOS_DIR = BASE_DIR / "sample_videos"
SERVICE_DIR = Path(__file__).parent

# Load .env file
load_dotenv(SERVICE_DIR / ".env")

# Environment configuration
class Settings:
    # Server settings
    PORT: int = int(os.getenv("PORT", "5001"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # Camera settings
    CAMERA_MODE: str = os.getenv("CAMERA_MODE", "simulated")  # simulated | live
    ENTRY_CAMERA_SOURCE: str = os.getenv(
        "ENTRY_CAMERA_SOURCE",
        str(SAMPLE_VIDEOS_DIR / "sample_video.mp4")
    )
    EXIT_CAMERA_SOURCE: str = os.getenv(
        "EXIT_CAMERA_SOURCE",
        str(SAMPLE_VIDEOS_DIR / "sample_video.mp4")
    )

    # Model paths
    YOLO_MODEL: str = str(MODELS_DIR / "yolov8n.pt")
    PLATE_DETECTOR_MODEL: str = str(MODELS_DIR / "license_plate_detector.pt")

    # Parking backend API
    PARKING_API_URL: str = os.getenv("PARKING_API_URL", "http://127.0.0.1:5000")

    # Detection settings
    MIN_CONFIDENCE: float = float(os.getenv("MIN_CONFIDENCE", "0.6"))
    DETECTION_COOLDOWN: int = int(os.getenv("DETECTION_COOLDOWN", "3"))  # seconds

    # Auto entry/exit mode
    AUTO_ENTRY_EXIT: bool = os.getenv("AUTO_ENTRY_EXIT", "false").lower() == "true"

    # Frame processing
    FRAME_SKIP: int = int(os.getenv("FRAME_SKIP", "2"))  # Process every nth frame
    FRAME_WIDTH: int = int(os.getenv("FRAME_WIDTH", "640"))
    FRAME_HEIGHT: int = int(os.getenv("FRAME_HEIGHT", "480"))
    JPEG_QUALITY: int = int(os.getenv("JPEG_QUALITY", "80"))

settings = Settings()
