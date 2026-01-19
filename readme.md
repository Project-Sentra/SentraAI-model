# SentraAI - License Plate Recognition Service

## Automated License Plate Recognition for Sentra Parking System

SentraAI is a FastAPI-based microservice that provides real-time license plate recognition capabilities for the Sentra Parking System. It uses YOLOv8 for vehicle detection and EasyOCR for plate text extraction, with specialized support for Sri Lankan license plate formats.

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  IP Camera /    │────▶│   SentraAI       │────▶│  Parking        │
│  Video Feed     │     │   Service        │     │  Backend        │
└─────────────────┘     │   (Port 5001)    │     │  (Port 5000)    │
                        └────────┬─────────┘     └─────────────────┘
                                 │
                        ┌────────▼─────────┐
                        │   WebSocket      │
                        │   Live Frames    │
                        └────────┬─────────┘
                                 │
                        ┌────────▼─────────┐
                        │  Admin Frontend  │
                        │  (Port 5173)     │
                        └──────────────────┘
```

---

## Features

- **Real-time Plate Detection**: Process video streams and detect license plates in real-time
- **Sri Lankan Plate Support**: Validates and formats Sri Lankan license plate formats:
  - Modern format: `WP CA-1234`, `WP CAB-1234`
  - Provincial numeric: `WP 1234`
  - Old format: `12-3456`
  - Special vehicles: `CAR 1234`, `GOV 1234`
- **WebSocket Streaming**: Live camera feeds with detection overlays
- **REST API**: Image-based detection endpoints
- **Parking Integration**: Automatic entry/exit logging with the parking backend
- **Simulated Mode**: Test with sample videos without physical cameras

---

## Project Structure

```
SentraAI-model/
├── service/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration settings
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment variables
│   ├── models/
│   │   ├── __init__.py
│   │   └── detector.py         # YOLO + EasyOCR wrapper
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── detect.py           # Detection API endpoints
│   │   └── cameras.py          # Camera management + WebSocket
│   ├── services/
│   │   ├── __init__.py
│   │   ├── plate_detector.py   # Core detection with deduplication
│   │   ├── camera_manager.py   # Camera stream management
│   │   └── parking_client.py   # Parking backend API client
│   └── utils/
│       ├── __init__.py
│       └── sri_lankan_plates.py # SL plate validation
├── models/
│   └── license_plate_detector.pt  # Custom plate detection model
├── sample_videos/
│   └── sample_video.mp4        # Test video for simulated mode
└── readme.md
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL (for parking backend)
- Node.js 18+ (for frontend)

### Installation

1. **Navigate to the service directory:**
   ```bash
   cd SentraAI-model/service
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   Edit `.env` file as needed:
   ```env
   PORT=5001
   CAMERA_MODE=simulated
   PARKING_API_URL=http://127.0.0.1:5000
   MIN_CONFIDENCE=0.6
   AUTO_ENTRY_EXIT=false
   ```

4. **Start the service:**
   ```bash
   uvicorn main:app --port 5001 --reload
   ```

---

## API Endpoints

### Health Check
```
GET /api/health
```
Returns service status and active camera count.

### Detection
```
POST /api/detect/image
```
Detect license plate from uploaded image file.

```
POST /api/detect/base64
```
Detect license plate from base64 encoded image.

### Camera Management
```
GET  /api/cameras              # List all cameras
POST /api/cameras/{id}/start   # Start camera stream
POST /api/cameras/{id}/stop    # Stop camera stream
POST /api/cameras/start-all    # Start all cameras
POST /api/cameras/stop-all     # Stop all cameras
```

### Entry/Exit Actions
```
POST /api/entry    # Confirm vehicle entry
POST /api/exit     # Confirm vehicle exit
```

### WebSocket
```
WS /api/ws
```
Real-time camera frames and detection events.

---

## WebSocket Events

### Server → Client

| Event | Description |
|-------|-------------|
| `cameras_list` | Initial list of configured cameras |
| `frame_update` | Live camera frame (base64 JPEG) |
| `plate_detected` | New plate detection event |
| `entry_result` | Result of entry confirmation |
| `exit_result` | Result of exit confirmation |
| `camera_status` | Camera status change |

### Client → Server

| Action | Description |
|--------|-------------|
| `start_camera` | Start specific camera |
| `stop_camera` | Stop specific camera |
| `start_all` | Start all cameras |
| `confirm_entry` | Confirm vehicle entry |
| `confirm_exit` | Confirm vehicle exit |

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 5001 | Service port |
| `HOST` | 0.0.0.0 | Service host |
| `DEBUG` | true | Enable debug mode |
| `CAMERA_MODE` | simulated | `simulated` or `live` |
| `ENTRY_CAMERA_SOURCE` | sample_video.mp4 | Entry camera source |
| `EXIT_CAMERA_SOURCE` | sample_video.mp4 | Exit camera source |
| `PARKING_API_URL` | http://127.0.0.1:5000 | Parking backend URL |
| `MIN_CONFIDENCE` | 0.6 | Minimum detection confidence |
| `DETECTION_COOLDOWN` | 3 | Seconds between same plate detections |
| `AUTO_ENTRY_EXIT` | false | Auto-process without confirmation |
| `FRAME_SKIP` | 2 | Process every nth frame |
| `FRAME_WIDTH` | 640 | Output frame width |
| `FRAME_HEIGHT` | 480 | Output frame height |
| `JPEG_QUALITY` | 80 | JPEG compression quality |

---

## Sri Lankan Plate Formats

The service supports the following Sri Lankan license plate formats:

| Format | Example | Description |
|--------|---------|-------------|
| Modern | `WP CAB-1234` | Province + 2-3 letters + 4 digits |
| Provincial | `WP 1234` | Province + 4 digits |
| Old | `12-3456` | 2-3 digits + 4 digits |
| Special | `CAR 1234` | 3 letters + 4 digits |

### Supported Province Codes
- WP - Western Province
- CP - Central Province
- SP - Southern Province
- NW - North Western Province
- NC - North Central Province
- UP - Uva Province
- SG - Sabaragamuwa Province
- EP - Eastern Province
- NP - Northern Province

---

## Integration with Parking System

SentraAI integrates with the LPR Parking System backend:

1. **Detection Flow:**
   - Camera captures frame → SentraAI detects plate → WebSocket notification → Frontend shows confirmation modal

2. **Entry Flow:**
   - Operator confirms entry → SentraAI calls `/api/vehicle/entry` → Parking spot assigned

3. **Exit Flow:**
   - Operator confirms exit → SentraAI calls `/api/vehicle/exit` → Duration & amount calculated

---

## Running the Full System

1. **Start Parking Backend (Terminal 1):**
   ```bash
   cd lpr-parking-system/admin_backend
   python app.py
   ```

2. **Start SentraAI Service (Terminal 2):**
   ```bash
   cd SentraAI-model/service
   uvicorn main:app --port 5001 --reload
   ```

3. **Start Frontend (Terminal 3):**
   ```bash
   cd lpr-parking-system/admin_frontend
   npm run dev
   ```

4. **Access the system:**
   - Frontend: http://localhost:5173
   - SentraAI API: http://localhost:5001
   - Parking API: http://localhost:5000

---

## Technologies Used

- **FastAPI** - Modern async Python web framework
- **YOLOv8** - State-of-the-art object detection
- **EasyOCR** - Optical character recognition
- **OpenCV** - Computer vision processing
- **WebSockets** - Real-time communication
- **httpx** - Async HTTP client

---

## License

Part of the Sentra Parking System project.
