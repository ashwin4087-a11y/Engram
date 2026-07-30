import os
import json
import time
import cv2
import numpy as np
import base64
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from src.infer import BallDetector
from src.utils import draw_detections

app = FastAPI(title="VisionBall API")

# LIVE CAMERA PIPELINE CONFIGURATION
LIVE_CONF_THRESHOLD = 0.60
LIVE_IOU_THRESHOLD = 0.45
BOX_MIN_PX = 15
BOX_MAX_FRAME_RATIO = 0.60
BOX_ASPECT_MIN = 0.4
BOX_ASPECT_MAX = 2.5

# Initialize detector once at startup (shared instance)
detector = BallDetector(model_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "best.onnx")))

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "stitch_visionball_enterprise_analytics_dashboard"))

_live_stats = {
    "fps": 0.0,
    "latency_ms": 0.0,
    "detections": 0,
    "highest_confidence": 0.0,
    "active": False,
    "last_active": 0.0
}


def get_html(page_name: str) -> str:
    path = os.path.join(FRONTEND_DIR, page_name, "code.html")
    if not os.path.exists(path):
        return f"<h1>404 - Not Found ({page_name})</h1>"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# Page routes (unchanged)
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return get_html("visionball_dashboard_updated")

@app.get("/image", response_class=HTMLResponse)
async def image_detection():
    return get_html("visionball_image_detection_updated")

@app.get("/live", response_class=HTMLResponse)
async def live_camera():
    return get_html("visionball_live_camera_updated")


# Metrics route (unchanged)
@app.get("/api/metrics")
async def get_metrics():
    metrics_path = os.path.join(os.path.dirname(__file__), "..", "results", "metrics.json")
    data = {}
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            data = json.load(f)

    model_name = os.path.basename(detector.model_path)
    backend_display = "ONNX Runtime" if detector.backend == "onnx" else "PyTorch" if detector.backend == "pytorch" else "Unknown"

    data["runtime_status"] = {
        "model": model_name,
        "backend": backend_display,
        "device": str(detector.device).upper(),
        "input_size": f"{detector.imgsz} × {detector.imgsz}",
        "version": "YOLOv11",
        "ready": True
    }
    return data


# Image detection endpoint (unchanged)
@app.post("/api/detect/image")
async def detect_image(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return JSONResponse({"error": "Invalid image"}, status_code=400)

    start_time = time.time()
    boxes, scores, class_ids = detector.predict(img)
    latency_ms = (time.time() - start_time) * 1000

    annotated = draw_detections(img, boxes, scores, class_ids)

    _, buffer = cv2.imencode(".jpg", annotated)
    b64_str = base64.b64encode(buffer).decode("utf-8")

    details = []
    for i in range(len(boxes)):
        details.append({
            "object": "Sports Ball",
            "confidence": round(float(scores[i]), 3),
            "box": [round(float(c), 1) for c in boxes[i]]
        })

    # Update live stats for dashboard runtime metrics
    _live_stats["latency_ms"] = round(latency_ms, 2)
    _live_stats["fps"] = round(1000.0 / latency_ms, 1) if latency_ms > 0 else 0.0
    _live_stats["detections"] = len(boxes)
    if len(scores) > 0:
        _live_stats["highest_confidence"] = round(max([float(s) for s in scores]), 3)
    _live_stats["last_active"] = time.time()

    return JSONResponse({
        "detections": len(boxes),
        "latency_ms": round(latency_ms, 2),
        "image_b64": "data:image/jpeg;base64," + b64_str,
        "details": details
    })


# Helper: geometric box filter
def filter_boxes(boxes, scores, class_ids, frame_shape):
    h, w = frame_shape[:2]
    fb, fs, fc = [], [], []
    for b, s, c in zip(boxes, scores, class_ids):
        x1, y1, x2, y2 = b
        bw, bh = x2 - x1, y2 - y1
        if bw < BOX_MIN_PX or bh < BOX_MIN_PX:
            continue
        if bw > w * BOX_MAX_FRAME_RATIO or bh > h * BOX_MAX_FRAME_RATIO:
            continue
        aspect = bw / bh if bh > 0 else 0
        if aspect < BOX_ASPECT_MIN or aspect > BOX_ASPECT_MAX:
            continue
        fb.append(b)
        fs.append(s)
        fc.append(c)
    return fb, fs, fc


# Live frame endpoint: accepts base64 JPEG frames from browser
@app.post("/api/detect/live/frame")
async def detect_live_frame(payload: dict):
    try:
        img_b64 = payload.get("image_b64")
        if not img_b64:
            raise ValueError("No image_b64 provided")

        if img_b64.startswith("data:"):
            img_b64 = img_b64.split(",", 1)[1]

        img_bytes = base64.b64decode(img_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Invalid image data")

        # Resize to 640x480 for consistent, fast inference
        frame = cv2.resize(frame, (640, 480))

        t0 = time.time()
        boxes, scores, class_ids = detector.predict(
            frame,
            conf_thres=LIVE_CONF_THRESHOLD,
            iou_thres=LIVE_IOU_THRESHOLD
        )
        boxes, scores, class_ids = filter_boxes(boxes, scores, class_ids, frame.shape)
        latency_ms = (time.time() - t0) * 1000

        details = []
        for i in range(len(boxes)):
            details.append({
                "object": "Sports Ball",
                "confidence": round(float(scores[i]), 3),
                "box": [round(float(c), 1) for c in boxes[i]]
            })

        # Update runtime stats
        _live_stats["latency_ms"] = round(latency_ms, 2)
        _live_stats["fps"] = round(1000.0 / latency_ms, 1) if latency_ms > 0 else 0.0
        _live_stats["detections"] = len(boxes)
        _live_stats["highest_confidence"] = round(max([float(s) for s in scores] + [0.0]), 3)
        _live_stats["active"] = True
        _live_stats["last_active"] = time.time()

        return JSONResponse({
            "detections": len(boxes),
            "latency_ms": round(latency_ms, 2),
            "details": details
        })

    except Exception as e:
        logger.error(f"/api/detect/live/frame error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/detect/live/stop")
async def stop_feed():
    logger.info(">>> /api/detect/live/stop called by client.")
    _live_stats["active"] = False
    return JSONResponse({"status": "stopped"})


@app.get("/api/detect/live_stats")
async def get_live_stats():
    _live_stats["last_polled"] = time.time()
    if _live_stats.get("active", False):
        last_active = _live_stats.get("last_active", 0)
        if last_active > 0 and (time.time() - last_active) > 10.0:
            logger.warning("Watchdog: Stream frozen for >10s. Marking inactive.")
            _live_stats["active"] = False
    return JSONResponse(_live_stats)
