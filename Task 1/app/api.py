import os
import sys
import json
import time
import cv2
import numpy as np
import base64
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse

# Add src/ to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from infer import BallDetector
from utils import draw_detections

app = FastAPI(title="VisionBall API")

# Initialize detector
detector = BallDetector(model_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "best.onnx")))

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "stitch_visionball_enterprise_analytics_dashboard"))

def get_html(page_name: str) -> str:
    path = os.path.join(FRONTEND_DIR, page_name, "code.html")
    if not os.path.exists(path):
        return f"<h1>404 - Not Found ({page_name})</h1>"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# --- Page Routes ---
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return get_html("visionball_dashboard_updated")

@app.get("/image", response_class=HTMLResponse)
async def image_detection():
    return get_html("visionball_image_detection_updated")

@app.get("/live", response_class=HTMLResponse)
async def live_camera():
    return get_html("visionball_live_camera_updated")


# --- API Endpoints ---
@app.get("/api/metrics")
async def get_metrics():
    metrics_path = os.path.join(os.path.dirname(__file__), "..", "results", "metrics.json")
    data = {}
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            data = json.load(f)
            
    # Inject runtime system status
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
    global _live_stats
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

_live_stats = {
    "fps": 0.0,
    "latency_ms": 0.0,
    "detections": 0,
    "highest_confidence": 0.0,
    "active": False,
    "last_active": 0.0
}

def generate_frames():
    global _live_stats
    _live_stats["active"] = True
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        # Fallback to dummy frames if no camera
        while True:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "No Camera Detected", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            ret, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(0.1)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        t0 = time.time()
        boxes, scores, class_ids = detector.predict(frame)
        latency = time.time() - t0
        fps = 1.0 / (latency + 1e-9)
        
        _live_stats["fps"] = round(fps, 1)
        _live_stats["latency_ms"] = round(latency * 1000, 1)
        _live_stats["detections"] = len(boxes)
        _live_stats["highest_confidence"] = round(max([float(s) for s in scores] + [0.0]), 3)
        _live_stats["last_active"] = time.time()
        
        annotated = draw_detections(frame, boxes, scores, class_ids, fps=fps)
        
        ret, buffer = cv2.imencode('.jpg', annotated)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
               
    _live_stats["active"] = False

@app.get("/api/detect/live")
async def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/detect/live_stats")
async def get_live_stats():
    return JSONResponse(_live_stats)
