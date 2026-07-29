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

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "stitch_visionball_enterprise_analytics_dashboard", "stitch_visionball_enterprise_analytics_dashboard"))

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

@app.get("/analytics", response_class=HTMLResponse)
async def analytics():
    return get_html("visionball_analytics_updated")

@app.get("/image", response_class=HTMLResponse)
async def image_detection():
    return get_html("visionball_image_detection_updated")

@app.get("/video", response_class=HTMLResponse)
async def video_detection():
    return get_html("visionball_video_detection_updated")

@app.get("/live", response_class=HTMLResponse)
async def live_camera():
    return get_html("visionball_live_camera_updated")

@app.get("/benchmark", response_class=HTMLResponse)
async def benchmark():
    return get_html("visionball_models_benchmarks_updated")


# --- API Endpoints ---
@app.get("/api/metrics")
async def get_metrics():
    metrics_path = os.path.join(os.path.dirname(__file__), "..", "results", "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            return json.load(f)
    return {}

@app.post("/api/detect/image")
async def detect_image(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return JSONResponse({"error": "Invalid image"}, status_code=400)
    
    start_time = time.time()
    boxes, scores, class_ids = detector.predict(img, conf_thres=0.15)
    latency_ms = (time.time() - start_time) * 1000
    
    annotated = draw_detections(img, boxes, scores, class_ids)
    
    _, buffer = cv2.imencode(".jpg", annotated)
    b64_str = base64.b64encode(buffer).decode("utf-8")
    
    return JSONResponse({
        "detections": len(boxes),
        "latency_ms": round(latency_ms, 2),
        "image_b64": "data:image/jpeg;base64," + b64_str
    })

def generate_frames():
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
        boxes, scores, class_ids = detector.predict(frame, conf_thres=0.15)
        fps = 1.0 / (time.time() - t0 + 1e-9)
        
        annotated = draw_detections(frame, boxes, scores, class_ids, fps=fps)
        
        ret, buffer = cv2.imencode('.jpg', annotated)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.get("/api/detect/live")
async def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")
