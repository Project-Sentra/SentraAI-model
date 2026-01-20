# 🤖 SentraAI - License Plate Recognition Service

## Automated License Plate Recognition for Sentra Parking System

SentraAI is a **FastAPI-based microservice** that provides real-time license plate recognition capabilities for the Sentra Parking System. It uses **YOLOv8** for vehicle detection and **EasyOCR** for plate text extraction, with specialized support for Sri Lankan license plate formats.

<div align="center">

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-orange.svg)](https://github.com/ultralytics/ultralytics)

</div>

---

## 🏗️ System Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  IP Camera /    │────▶│   SentraAI       │────▶│  Parking        │
│  Video Feed     │     │   Service        │     │  Backend        │
│  (Entry/Exit)   │     │   (Port 5001)    │     │  (Port 5000)    │
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                 │
                        ┌────────▼─────────┐
                        │   WebSocket      │
                        │   Live Frames    │
                        │   + Detections   │
                        └────────┬─────────┘
                                 │
                        ┌────────▼─────────┐
                        │  Admin Frontend  │
                        │  (Port 5173)     │
                        └──────────────────┘
```

**Flow:**
1. Camera feed → SentraAI detects plate
2. SentraAI sends WebSocket notification to frontend
3. Operator confirms entry/exit
4. SentraAI calls parking backend API
5. Dashboard updates in real-time

---

## ✨ Features

- ✅ **Real-time Plate Detection** - Process video streams and detect license plates instantly
- 🇱🇰 **Sri Lankan Plate Support** - Validates and formats all SL plate formats
- 🔌 **WebSocket Streaming** - Live camera feeds with detection overlays
- 🎯 **REST API** - Image-based detection endpoints
- 🔗 **Parking Integration** - Automatic entry/exit logging
- 🎬 **Simulated Mode** - Test with sample videos without physical cameras
- 🔄 **Smart Deduplication** - Prevents duplicate detections (3s cooldown)
- 📊 **Confidence Scoring** - Only accepts high-confidence detections (>60%)
- 🚀 **Async Processing** - Non-blocking camera stream handling

---

## 📦 Prerequisites

Before installation, ensure you have:

- **Python 3.10+** - [Download](https://www.python.org/downloads/)
- **Git** - [Download](https://git-scm.com/downloads/)
- **FFmpeg** (for video processing) - [Download](https://ffmpeg.org/download.html)
  ```bash
  # macOS
  brew install ffmpeg
  
  # Ubuntu/Debian
  sudo apt install ffmpeg
  
  # Windows
  # Download from ffmpeg.org and add to PATH
  ```

---

## 🚀 Quick Start Guide

### Step 1: Clone the Repository

```bash
git clone https://github.com/Project-Sentra/SentraAI-model.git
cd SentraAI-model
```

### Step 2: Navigate to Service Directory

```bash
cd service
```

### Step 3: Create Virtual Environment (Recommended)

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** This will download:
- FastAPI & Uvicorn (web server)
- Ultralytics (YOLOv8)
- EasyOCR (optical character recognition)
- OpenCV (computer vision)
- httpx (async HTTP client)

Installation may take 5-10 minutes as it downloads ML models.

### Step 5: Verify Model Files

Ensure these model files exist:

```
SentraAI-model/
├── models/
│   └── license_plate_detector.pt   ✅ Should exist
└── service/
    └── yolov8n.pt                   ✅ Should exist
```

If missing, YOLOv8n will auto-download on first run. For the custom plate detector, ensure it's included in the repository.

### Step 6: Configure Environment

The default `.env` file should work for testing:

```env
# Server settings
PORT=5001
HOST=0.0.0.0
DEBUG=true

# Camera mode: simulated | live
CAMERA_MODE=simulated

# Parking system backend URL
PARKING_API_URL=http://127.0.0.1:5000

# Detection settings
MIN_CONFIDENCE=0.6
AUTO_ENTRY_EXIT=false
```

**Don't change anything yet** - these defaults enable simulated mode for testing!

### Step 7: Start the Service

```bash
uvicorn main:app --port 5001 --reload
```

✅ **You should see:**
```
==================================================
SentraAI Service Starting...
Camera Mode: simulated
Parking API: http://127.0.0.1:5000
Min Confidence: 0.6
Auto Entry/Exit: False
==================================================
INFO:     Uvicorn running on http://0.0.0.0:5001
INFO:     Application startup complete.
```

### Step 8: Test the Service

Open your browser and navigate to:
- **API Docs:** http://localhost:5001/docs
- **Health Check:** http://localhost:5001/api/health

Expected response:
```json
{
  "status": "healthy",
  "service": "SentraAI",
  "version": "1.0.0",
  "camera_mode": "simulated",
  "cameras_active": 0
}
```

---

## 📖 Complete Setup Guide

### Running with Simulated Cameras (Testing)

1. **Start the parking backend first:**
   ```bash
   # In a separate terminal
   cd ../lpr-parking-system/admin_backend
   python app.py
   ```

2. **Start SentraAI service:**
   ```bash
   cd SentraAI-model/service
   uvicorn main:app --port 5001 --reload
   ```

3. **Start the frontend:**
   ```bash
   # In another terminal
   cd ../lpr-parking-system/admin_frontend
   npm run dev
   ```

4. **Access the dashboard:** http://localhost:5173

5. **Start camera feed:**
   - Click "Start Camera" button in the dashboard
   - The service will process `sample_videos/sample_video.mp4`
   - Detected plates will appear in confirmation modals

### Running with Live IP Cameras (Production)

1. **Edit `.env` file:**
   ```env
   CAMERA_MODE=live
   ENTRY_CAMERA_SOURCE=rtsp://username:password@192.168.1.100:554/stream1
   EXIT_CAMERA_SOURCE=rtsp://username:password@192.168.1.101:554/stream1
   ```

2. **Common IP camera URL formats:**
   - **RTSP:** `rtsp://user:pass@ip:port/path`
   - **HTTP:** `http://ip:port/video`
   - **ONVIF:** `rtsp://ip:554/onvif1`

3. **Test camera connectivity:**
   ```bash
   ffplay "rtsp://your-camera-url"
   ```

4. **Restart the service**

### Camera Configuration Examples

#### HIKVision:
```env
ENTRY_CAMERA_SOURCE=rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101
```

#### Dahua:
```env
ENTRY_CAMERA_SOURCE=rtsp://admin:password@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0
```

#### Generic MJPEG:
```env
ENTRY_CAMERA_SOURCE=http://192.168.1.50:8080/video
```

---

## 🔌 API Reference

### Health & Status

#### Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "SentraAI",
  "version": "1.0.0",
  "camera_mode": "simulated",
  "cameras_active": 0
}
```

### Image Detection

#### Detect from Uploaded Image
```http
POST /api/detect/image
Content-Type: multipart/form-data

file: <image_file>
```

**Response:**
```json
{
  "success": true,
  "plate_number": "WP CA-1234",
  "confidence": 0.87,
  "formatted_plate": "WP CA-1234",
  "is_valid_sl_plate": true,
  "raw_text": "WPCA1234"
}
```

#### Detect from Base64
```http
POST /api/detect/base64
Content-Type: application/json

{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

### Camera Management

#### List Cameras
```http
GET /api/cameras
```

#### Start Camera
```http
POST /api/cameras/{camera_id}/start
```

#### Stop Camera
```http
POST /api/cameras/{camera_id}/stop
```

#### Start All Cameras
```http
POST /api/cameras/start-all
```

#### Stop All Cameras
```http
POST /api/cameras/stop-all
```

### Entry/Exit Actions

#### Confirm Entry
```http
POST /api/entry
Content-Type: application/json

{
  "plate_number": "WP CA-1234"
}
```

#### Confirm Exit
```http
POST /api/exit
Content-Type: application/json

{
  "plate_number": "WP CA-1234"
}
```

---

## 🔄 WebSocket Protocol

### Connection
```javascript
const ws = new WebSocket('ws://localhost:5001/api/ws');
```

### Server → Client Events

#### Initial Camera List
```json
{
  "type": "cameras_list",
  "cameras": [
    {
      "id": "entry",
      "name": "Entry Camera",
      "type": "entry",
      "active": false
    }
  ]
}
```

#### Live Frame Update
```json
{
  "type": "frame_update",
  "camera_id": "entry",
  "frame": "<base64_jpeg_image>",
  "timestamp": "2026-01-20T15:30:00"
}
```

#### Plate Detected
```json
{
  "type": "plate_detected",
  "camera_id": "entry",
  "camera_type": "entry",
  "plate_number": "WP CA-1234",
  "confidence": 0.87,
  "formatted_plate": "WP CA-1234",
  "is_valid": true,
  "detected_at": "2026-01-20T15:30:00"
}
```

#### Entry/Exit Result
```json
{
  "type": "entry_result",
  "success": true,
  "message": "Vehicle entered successfully",
  "data": {
    "plate_number": "WP CA-1234",
    "spot_name": "A01"
  }
}
```

### Client → Server Actions

#### Start Camera
```json
{
  "action": "start_camera",
  "camera_id": "entry"
}
```

#### Confirm Entry
```json
{
  "action": "confirm_entry",
  "plate_number": "WP CA-1234"
}
```

#### Confirm Exit
```json
{
  "action": "confirm_exit",
  "plate_number": "WP CA-1234"
}
```

---

## 🇱🇰 Sri Lankan License Plate Formats

The service automatically validates and formats all Sri Lankan plate types:

| Format | Example | Description | Regex Pattern |
|--------|---------|-------------|---------------|
| **Modern** | `WP CAB-1234` | Province + 2-3 letters + 4 digits | `[A-Z]{2}\s?[A-Z]{2,3}-?\d{4}` |
| **Provincial** | `WP 1234` | Province + 4 digits | `[A-Z]{2}\s?\d{4}` |
| **Old Format** | `12-3456` | 2-3 digits + 4 digits | `\d{2,3}-?\d{4}` |
| **Special** | `CAR 1234` | 3 letters + 4 digits | `[A-Z]{3}\s?\d{4}` |

### Supported Province Codes
- `WP` - Western Province
- `CP` - Central Province  
- `SP` - Southern Province
- `NW` - North Western Province
- `NC` - North Central Province
- `UP` - Uva Province
- `SG` - Sabaragamuwa Province
- `EP` - Eastern Province
- `NP` - Northern Province

### Examples of Valid Plates
```
WP CA-1234  →  WP CA-1234
WPCA1234    →  WP CA-1234
WP1234      →  WP 1234
12-3456     →  12-3456
CAR1234     →  CAR 1234
GOV1234     →  GOV 1234
```

---
---

## ⚙️ Configuration Reference

### Environment Variables

| Variable | Default | Options | Description |
|----------|---------|---------|-------------|
| `PORT` | `5001` | Any port | Service port number |
| `HOST` | `0.0.0.0` | IP address | Service host (0.0.0.0 = all interfaces) |
| `DEBUG` | `true` | true/false | Enable debug logging |
| `CAMERA_MODE` | `simulated` | simulated/live | Camera source mode |
| `ENTRY_CAMERA_SOURCE` | `../sample_videos/sample_video.mp4` | File path or URL | Entry camera source |
| `EXIT_CAMERA_SOURCE` | `../sample_videos/sample_video.mp4` | File path or URL | Exit camera source |
| `PARKING_API_URL` | `http://127.0.0.1:5000` | URL | Parking backend API URL |
| `MIN_CONFIDENCE` | `0.6` | 0.0-1.0 | Minimum detection confidence threshold |
| `DETECTION_COOLDOWN` | `3` | Seconds | Prevent duplicate detections |
| `AUTO_ENTRY_EXIT` | `false` | true/false | Auto-process without confirmation |
| `FRAME_SKIP` | `2` | Integer | Process every nth frame (performance) |
| `FRAME_WIDTH` | `640` | Pixels | Output frame width |
| `FRAME_HEIGHT` | `480` | Pixels | Output frame height |
| `JPEG_QUALITY` | `80` | 1-100 | JPEG compression quality |

### Configuration Examples

#### High Accuracy Mode (Slower)
```env
MIN_CONFIDENCE=0.8
FRAME_SKIP=1
FRAME_WIDTH=1280
FRAME_HEIGHT=720
```

#### Performance Mode (Faster)
```env
MIN_CONFIDENCE=0.6
FRAME_SKIP=3
FRAME_WIDTH=480
FRAME_HEIGHT=360
```

#### Auto-Entry Mode (No Confirmation)
```env
AUTO_ENTRY_EXIT=true
DETECTION_COOLDOWN=5
```

---

## 📁 Project Structure

```
SentraAI-model/
├── service/                           # Main service directory
│   ├── main.py                        # FastAPI application entry point
│   ├── config.py                      # Configuration settings & env vars
│   ├── requirements.txt               # Python dependencies
│   ├── .env                           # Environment configuration
│   ├── yolov8n.pt                     # YOLOv8 nano model (general detection)
│   │
│   ├── models/                        # ML models package
│   │   ├── __init__.py
│   │   └── detector.py                # YOLO + EasyOCR wrapper class
│   │
│   ├── routers/                       # FastAPI route handlers
│   │   ├── __init__.py
│   │   ├── detect.py                  # Detection API endpoints
│   │   └── cameras.py                 # Camera mgmt + WebSocket handler
│   │
│   ├── services/                      # Business logic layer
│   │   ├── __init__.py
│   │   ├── plate_detector.py          # Core detection with deduplication
│   │   ├── camera_manager.py          # Camera stream management
│   │   └── parking_client.py          # Parking backend API client
│   │
│   └── utils/                         # Helper utilities
│       ├── __init__.py
│       └── sri_lankan_plates.py       # SL plate validation & formatting
│
├── models/                            # Trained model files
│   └── license_plate_detector.pt      # Custom license plate detector model
│
├── sample_videos/                     # Test videos
│   └── sample_video.mp4               # Sample video for simulated mode
│
├── app/                               # (Legacy) Streamlit demo app
│   ├── app.py                         # Streamlit dashboard
│   ├── process_video.py               # Video processing utilities
│   ├── visualize.py                   # Visualization functions
│   └── ...
│
├── readme.md                          # This file
├── requirements.txt                   # Root dependencies (for app/)
└── setup.sh                           # Setup script
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Module Import Errors
```
ModuleNotFoundError: No module named 'fastapi'
```
**Solution:**
- Ensure virtual environment is activated: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

#### 2. Camera Connection Failed
```
ERROR: Failed to open camera source
```
**Solutions:**
- **Simulated mode:** Verify `sample_videos/sample_video.mp4` exists
- **Live mode:** Test camera URL with `ffplay rtsp://your-camera-url`
- Check camera credentials and network connectivity
- Verify firewall allows RTSP port (usually 554)

#### 3. Model File Not Found
```
FileNotFoundError: models/license_plate_detector.pt
```
**Solution:**
- Ensure model file exists in `SentraAI-model/models/`
- If missing, restore from repository or retrain model

#### 4. Parking Backend Connection Failed
```
ERROR: Failed to connect to parking API
```
**Solutions:**
- Ensure parking backend is running: `python app.py` in `admin_backend/`
- Verify `PARKING_API_URL` matches backend address
- Check firewall/network allows port 5000

#### 5. Low Detection Accuracy
**Solutions:**
- Improve camera positioning (front-facing, well-lit)
- Increase `MIN_CONFIDENCE` threshold
- Reduce `FRAME_SKIP` to process more frames
- Ensure plates are clearly visible (not blurry/occluded)
- Clean camera lens

#### 6. High CPU/Memory Usage
**Solutions:**
- Increase `FRAME_SKIP` to process fewer frames
- Reduce `FRAME_WIDTH` and `FRAME_HEIGHT`
- Lower `JPEG_QUALITY` for WebSocket streaming
- Use GPU if available (requires `torch` with CUDA)

#### 7. Port Already in Use
```
ERROR: [Errno 48] Address already in use
```
**Solution:**
```bash
# Find process using port 5001
lsof -ti:5001 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :5001   # Windows

# Or change PORT in .env
```

#### 8. WebSocket Connection Drops
**Solutions:**
- Check network stability
- Reduce frame rate (increase `FRAME_SKIP`)
- Lower video quality settings
- Ensure adequate bandwidth

---

## 🚀 Running the Full Sentra System

### Complete Startup Sequence

**1. Start Parking Backend (Terminal 1):**
```bash
cd lpr-parking-system/admin_backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python app.py
```
**✅ Wait for:** `Server starting on port 5000...`

**2. Start SentraAI Service (Terminal 2):**
```bash
cd SentraAI-model/service
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn main:app --port 5001 --reload
```
**✅ Wait for:** `SentraAI Service Starting...`

**3. Start Admin Frontend (Terminal 3):**
```bash
cd lpr-parking-system/admin_frontend
npm run dev
```
**✅ Wait for:** `Local: http://localhost:5173`

**4. Access the System:**
- 🖥️ **Admin Dashboard:** http://localhost:5173
- 🤖 **SentraAI API Docs:** http://localhost:5001/docs
- 🔧 **Backend API:** http://localhost:5000

### Testing the System

1. Open dashboard at http://localhost:5173
2. Click "Start Camera" button
3. Watch live feed with detection overlays
4. When a plate is detected, confirmation modal appears
5. Click "Confirm Entry" or "Confirm Exit"
6. Dashboard updates automatically!

---

## 🔧 Advanced Configuration

### Using GPU Acceleration

For faster processing with NVIDIA GPU:

1. **Install CUDA toolkit:**
   - Download from [NVIDIA website](https://developer.nvidia.com/cuda-downloads)

2. **Install PyTorch with CUDA:**
   ```bash
   pip uninstall torch torchvision
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

3. **Verify GPU is detected:**
   ```python
   import torch
   print(torch.cuda.is_available())  # Should print True
   ```

### Custom Model Training

To train your own license plate detector:

1. **Collect training data** (images with labeled plates)
2. **Use YOLOv8 training:**
   ```bash
   yolo detect train data=plates.yaml model=yolov8n.pt epochs=100
   ```
3. **Replace model file:**
   ```bash
   cp runs/detect/train/weights/best.pt models/license_plate_detector.pt
   ```

### Multi-Camera Setup

To add more cameras, edit `service/services/camera_manager.py`:

```python
self.cameras = {
    "entry": Camera("entry", "Entry Camera", "entry", entry_source),
    "exit": Camera("exit", "Exit Camera", "exit", exit_source),
    "entry2": Camera("entry2", "Entry Camera 2", "entry", entry2_source),
    "parking_lot": Camera("parking_lot", "Parking Lot", "monitor", lot_source),
}
```

Add corresponding environment variables:
```env
ENTRY2_CAMERA_SOURCE=rtsp://...
PARKING_LOT_CAMERA_SOURCE=rtsp://...
```

---

## 🧪 Testing & Development

### Run Unit Tests
```bash
pytest tests/
```

### Manual API Testing

**Test image detection:**
```bash
curl -X POST "http://localhost:5001/api/detect/image" \
  -F "file=@test_plate.jpg"
```

**Test health endpoint:**
```bash
curl http://localhost:5001/api/health
```

### Load Testing

Use Apache Bench or Locust for performance testing:
```bash
ab -n 1000 -c 10 http://localhost:5001/api/health
```

---

## 📊 Performance Optimization

### Recommended Settings by Hardware

#### Low-End (Raspberry Pi, Intel i3)
```env
FRAME_SKIP=5
FRAME_WIDTH=480
FRAME_HEIGHT=360
MIN_CONFIDENCE=0.7
JPEG_QUALITY=70
```

#### Mid-Range (Intel i5/i7, AMD Ryzen 5)
```env
FRAME_SKIP=2
FRAME_WIDTH=640
FRAME_HEIGHT=480
MIN_CONFIDENCE=0.6
JPEG_QUALITY=80
```

#### High-End (With GPU)
```env
FRAME_SKIP=1
FRAME_WIDTH=1280
FRAME_HEIGHT=720
MIN_CONFIDENCE=0.5
JPEG_QUALITY=90
```

---

## 🔐 Security Considerations

**⚠️ For Production Deployment:**

1. **Secure camera credentials:**
   - Never commit camera URLs with passwords to git
   - Use environment variables or secret management

2. **Enable HTTPS:**
   - Use reverse proxy (nginx) with SSL certificate
   - Update WebSocket to use WSS protocol

3. **Add authentication:**
   - Implement API key authentication
   - Use JWT tokens for WebSocket connections

4. **Network security:**
   - Place cameras on isolated VLAN
   - Use VPN for remote access
   - Implement rate limiting

5. **Data privacy:**
   - Comply with GDPR/local privacy laws
   - Encrypt stored images
   - Implement data retention policies

---

## 📚 Technologies Used

| Technology | Purpose | Version |
|------------|---------|---------|
| **FastAPI** | Async web framework | 0.104+ |
| **YOLOv8** | Object detection | 8.0+ |
| **EasyOCR** | Text recognition | 1.7+ |
| **OpenCV** | Computer vision | 4.8+ |
| **Uvicorn** | ASGI server | 0.24+ |
| **WebSockets** | Real-time communication | 12.0+ |
| **httpx** | Async HTTP client | 0.25+ |
| **Pillow** | Image processing | 10.0+ |
| **NumPy** | Numerical operations | 1.24+ |

---

## 🔗 Related Repositories

- **[lpr-parking-system](https://github.com/Project-Sentra/lpr-parking-system)** - Admin dashboard & backend API
- **[Sentra-Mobile-App](https://github.com/Theek237/Sentra-Mobile-App)** - Flutter mobile application
- **[Sentra-Infrastructure](https://github.com/Project-Sentra/Sentra-Infrastructure)** - Deployment & IaC

---

## 📝 License

Part of the Sentra Parking System ecosystem.

---

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Support for other countries' license plate formats
- Improved detection accuracy
- Additional camera protocols (ONVIF, etc.)
- Performance optimizations
- Unit test coverage

---

## 📞 Support & Issues

If you encounter issues:

1. **Check logs:** Terminal output shows detailed error messages
2. **Verify configuration:** Double-check `.env` settings
3. **Test components:** Use API docs at `/docs` for manual testing
4. **Review troubleshooting:** See section above

---

## 📈 Roadmap

- [ ] Multi-language plate support (India, UK, US)
- [ ] Vehicle classification (car, truck, motorcycle)
- [ ] Cloud deployment guides (AWS, Azure, GCP)
- [ ] Docker containerization
- [ ] Kubernetes manifests
- [ ] Performance metrics dashboard
- [ ] Advanced analytics (peak hours, trends)

---

<div align="center">

**Made with ❤️ by the Sentra Team**

[![GitHub stars](https://img.shields.io/github/stars/Project-Sentra/SentraAI-model?style=social)](https://github.com/Project-Sentra/SentraAI-model)

</div>
