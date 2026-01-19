"""
SentraAI Service - FastAPI Entry Point
License Plate Recognition Microservice
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import detect, cameras
from services.camera_manager import camera_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    print("=" * 50)
    print("SentraAI Service Starting...")
    print(f"Camera Mode: {settings.CAMERA_MODE}")
    print(f"Parking API: {settings.PARKING_API_URL}")
    print(f"Min Confidence: {settings.MIN_CONFIDENCE}")
    print(f"Auto Entry/Exit: {settings.AUTO_ENTRY_EXIT}")
    print("=" * 50)

    # Initialize cameras on startup
    await camera_manager.initialize()

    yield

    # Cleanup on shutdown
    print("Shutting down SentraAI Service...")
    await camera_manager.cleanup()


app = FastAPI(
    title="SentraAI",
    description="License Plate Recognition Service for Sentra Parking System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(detect.router, prefix="/api", tags=["Detection"])
app.include_router(cameras.router, prefix="/api", tags=["Cameras"])


@app.get("/api/health")
async def health_check():
    """Service health check endpoint"""
    return {
        "status": "healthy",
        "service": "SentraAI",
        "version": "1.0.0",
        "camera_mode": settings.CAMERA_MODE,
        "cameras_active": camera_manager.get_active_count()
    }


@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "SentraAI",
        "description": "License Plate Recognition Microservice",
        "endpoints": {
            "health": "/api/health",
            "detect": "/api/detect/image",
            "cameras": "/api/cameras",
            "websocket": "/ws"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
