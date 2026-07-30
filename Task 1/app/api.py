import os
import sys
import json
import time
import threading
import cv2
import numpy as np
import base64
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from src.infer import BallDetector
from src.utils import draw_detections

app = FastAPI(title="VisionBall API")

# ═══════════════════════════════════════════════════════════════════
# LIVE CAMERA PIPELINE CONFIGURATION
# These values ONLY affect /api/detect/live. Image detection is unchanged.
# ═══════════════════════════════════════════════════════════════════
LIVE_CONF_THRESHOLD = 0.60          # Runtime confidence (0.55–0.65 range)
LIVE_IOU_THRESHOLD = 0.45           # NMS IoU threshold
BOX_MIN_PX = 15                     # Minimum box width/height in pixels
BOX_MAX_FRAME_RATIO = 0.60          # Max box size as fraction of frame
BOX_ASPECT_MIN = 0.4                # Min width/height ratio
BOX_ASPECT_MAX = 2.5                # Max width/height ratio
TRACKER_IOU_THRESH = 0.3            # IoU to match detections across frames
TRACKER_MIN_HITS = 3                # Consecutive frames before showing box
TRACKER_MAX_LOST = 3                # Consecutive misses before removing box
INFER_EVERY_N = 2                    # Run YOLO every Nth frame (display all)

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

def filter_boxes(boxes, scores, class_ids, frame_shape):
    """Reject bounding boxes that are geometrically unrealistic for a ball."""
    h, w = frame_shape[:2]
    fb, fs, fc = [], [], []
    for b, s, c in zip(boxes, scores, class_ids):
        x1, y1, x2, y2 = b
        bw, bh = x2 - x1, y2 - y1
        # Too small — likely noise
        if bw < BOX_MIN_PX or bh < BOX_MIN_PX:
            continue
        # Too large — covering most of the frame
        if bw > w * BOX_MAX_FRAME_RATIO or bh > h * BOX_MAX_FRAME_RATIO:
            continue
        # Aspect ratio check — balls are roughly round
        aspect = bw / bh if bh > 0 else 0
        if aspect < BOX_ASPECT_MIN or aspect > BOX_ASPECT_MAX:
            continue
        fb.append(b)
        fs.append(s)
        fc.append(c)
    return fb, fs, fc

class SimpleTracker:
    """IoU-based frame-to-frame tracker for temporal stability.
    Requires min_hits consecutive detections before displaying.
    Removes tracks after max_lost consecutive misses."""
    def __init__(self, iou_thresh=TRACKER_IOU_THRESH,
                 max_lost=TRACKER_MAX_LOST, min_hits=TRACKER_MIN_HITS):
        self.iou_thresh = iou_thresh
        self.max_lost = max_lost
        self.min_hits = min_hits
        self.tracks = []

    def compute_iou(self, boxA, boxB):
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        interArea = max(0, xB - xA) * max(0, yB - yA)
        if interArea == 0: return 0.0
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        return interArea / float(boxAArea + boxBArea - interArea)

    def update(self, boxes, scores):
        matched_tracks = set()
        matched_dets = set()
        for i, det in enumerate(boxes):
            best_iou = 0
            best_trk = -1
            for j, trk in enumerate(self.tracks):
                if j in matched_tracks: continue
                iou = self.compute_iou(det, trk['box'])
                if iou > best_iou:
                    best_iou = iou
                    best_trk = j
            if best_iou >= self.iou_thresh:
                matched_tracks.add(best_trk)
                matched_dets.add(i)
                self.tracks[best_trk]['box'] = det
                self.tracks[best_trk]['score'] = scores[i]
                self.tracks[best_trk]['hits'] += 1
                self.tracks[best_trk]['lost'] = 0

        for i, det in enumerate(boxes):
            if i not in matched_dets:
                self.tracks.append({'box': det, 'score': scores[i], 'hits': 1, 'lost': 0})
                
        for j in range(len(self.tracks)):
            if j not in matched_tracks:
                self.tracks[j]['lost'] += 1
                
        self.tracks = [t for t in self.tracks if t['lost'] <= self.max_lost]
        
        valid_boxes, valid_scores = [], []
        for t in self.tracks:
            if t['hits'] >= self.min_hits:
                valid_boxes.append(t['box'])
                valid_scores.append(t['score'])
                
        return valid_boxes, valid_scores
                
class CameraManager:
    """Safely manages OpenCV VideoCapture in a single dedicated thread.

    Key design decisions:
    - cap is stored as self.cap so stop() can force-release it to unblock
      a stuck cap.read() on Windows MSMF.
    - DirectShow (CAP_DSHOW) is tried first on Windows because the default
      MSMF backend can block cap.read() for 10-15 seconds during initial
      format negotiation, making the camera appear unresponsive.
    - All state (cap, frame, thread) is fully reset in stop() so the next
      start() always begins from a clean slate.
    """

    def __init__(self):
        self.cap = None
        self.frame = None
        self.running = False
        self.lock = threading.Lock()
        self.thread = None

    def start(self):
        # If already running with a live thread, reuse it
        if self.running and self.thread is not None and self.thread.is_alive():
            logger.info("CameraManager: Already running, reusing existing session.")
            return
        # Clean up any stale state from a previous session
        self._cleanup()
        self.running = True
        self.frame = None
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logger.info("CameraManager: Capture thread launched.")

    def _cleanup(self):
        """Release camera hardware and reset state. Safe to call multiple times."""
        with self.lock:
            if self.cap is not None:
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None
            self.frame = None

    def _capture_loop(self):
        cap = None
        try:
            # Use DirectShow on Windows to avoid MSMF 15-second negotiation
            logger.info("CameraManager: Opening camera with DirectShow backend...")
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not cap.isOpened():
                logger.warning("CameraManager: DirectShow failed, trying default backend...")
                cap.release()
                cap = cv2.VideoCapture(0)

            if not cap.isOpened():
                logger.error("CameraManager: Camera FAILED to open. Aborting.")
                return

            # Set resolution before first read to prevent runtime renegotiation
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            try:
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            except Exception:
                pass

            # Store cap so stop() can force-release it
            with self.lock:
                self.cap = cap

            actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            logger.info(f"CameraManager: Camera OPENED. Resolution={actual_w}x{actual_h}")

            consecutive_failures = 0
            while self.running:
                ret, frame = cap.read()
                if not self.running:
                    break
                if ret and frame is not None:
                    consecutive_failures = 0
                    if frame.shape[1] != 640 or frame.shape[0] != 480:
                        frame = cv2.resize(frame, (640, 480))
                    with self.lock:
                        self.frame = frame
                else:
                    consecutive_failures += 1
                    if consecutive_failures > 200:
                        logger.error("CameraManager: 200 consecutive read failures. Exiting.")
                        break
                    time.sleep(0.01)

        except Exception as e:
            logger.error(f"CameraManager: Capture loop crashed: {e}")
        finally:
            # Always release hardware
            if cap is not None:
                try:
                    cap.release()
                    logger.info("CameraManager: Camera hardware RELEASED (LED should turn OFF).")
                except Exception:
                    pass
            with self.lock:
                self.cap = None
                self.running = False
                self.frame = None
            cv2.destroyAllWindows()
            logger.info("CameraManager: Capture thread exited cleanly.")

    def read(self):
        with self.lock:
            if self.frame is not None:
                return True, self.frame.copy()
            return False, None

    def stop(self):
        logger.info("CameraManager: Stop requested.")
        self.running = False
        # Force-release camera to unblock any stuck cap.read()
        with self.lock:
            if self.cap is not None:
                try:
                    self.cap.release()
                    logger.info("CameraManager: Force-released camera from stop().")
                except Exception as e:
                    logger.warning(f"CameraManager: Release error in stop(): {e}")
                self.cap = None
        # Wait for thread to finish
        if self.thread is not None and self.thread.is_alive():
            self.thread.join(timeout=3.0)
            if self.thread.is_alive():
                logger.warning("CameraManager: Thread did not join in 3s (daemon, will die at exit).")
            else:
                logger.info("CameraManager: Thread joined successfully.")
        with self.lock:
            self.frame = None
        self.thread = None
        cv2.destroyAllWindows()
        logger.info("CameraManager: Stop complete.")

cam_manager = CameraManager()

class InferenceWorker:
    """Runs YOLO inference in a background thread so the camera stream doesn't lag."""
    def __init__(self, detector, tracker):
        self.detector = detector
        self.tracker = tracker
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        
        self.frame_to_process = None
        self.cached_boxes = []
        self.cached_scores = []
        self.cached_class_ids = []
        self.last_infer_ms = 0.0

    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def update(self, frame):
        # We don't block. If the worker is still processing an old frame, 
        # this will just overwrite the pending frame with the latest one.
        with self.lock:
            self.frame_to_process = frame

    def get_results(self):
        with self.lock:
            return self.cached_boxes, self.cached_scores, self.cached_class_ids, self.last_infer_ms

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)

    def _loop(self):
        while self.running:
            frame = None
            with self.lock:
                if self.frame_to_process is not None:
                    frame = self.frame_to_process
                    self.frame_to_process = None
            
            if frame is None:
                time.sleep(0.01)
                continue
                
            try:
                t0 = time.time()
                boxes, scores, class_ids = self.detector.predict(
                    frame,
                    conf_thres=LIVE_CONF_THRESHOLD,
                    iou_thres=LIVE_IOU_THRESHOLD
                )
                boxes, scores, class_ids = filter_boxes(boxes, scores, class_ids, frame.shape)
                valid_boxes, valid_scores = self.tracker.update(boxes, scores)
                
                with self.lock:
                    self.cached_boxes = valid_boxes
                    self.cached_scores = valid_scores
                    self.cached_class_ids = [0] * len(valid_boxes)
                    self.last_infer_ms = (time.time() - t0) * 1000
            except Exception as e:
                logger.error(f"InferenceWorker error: {e}")

def generate_frames():
    """MJPEG generator with frame-skip inference decoupled to a background thread."""
    global _live_stats
    now = time.time()
    _live_stats["active"] = True
    _live_stats["last_active"] = now   # CRITICAL: prevents watchdog from killing on first poll
    _live_stats["last_polled"] = now
    logger.info(">>> STREAMING: Frame Generator Started")

    cam_manager.start()
    logger.info(">>> STREAMING: CameraManager.start() returned")

    tracker = SimpleTracker()
    infer_worker = InferenceWorker(detector, tracker)
    infer_worker.start()

    frame_count = 0
    prev_time = time.time()

    try:
        while _live_stats["active"]:
            ret, frame = cam_manager.read()
            if not ret or frame is None:
                # Keep watchdog alive during camera warm-up
                _live_stats["last_active"] = time.time()
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, "Camera Starting...", (150, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                ret, buffer = cv2.imencode('.jpg', frame)
                if ret:
                    yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
                           + buffer.tobytes() + b'\r\n')
                time.sleep(0.1)
                continue

            frame_count += 1

            # ── Send every Nth frame to the background worker ────────
            if frame_count % INFER_EVERY_N == 0:
                infer_worker.update(frame.copy())
            
            # ── Retrieve latest available predictions ────────────────
            cached_boxes, cached_scores, cached_class_ids, last_infer_ms = infer_worker.get_results()

            # ── FPS from wall-clock time between yields ────────────
            now = time.time()
            fps = 1.0 / (now - prev_time + 1e-9)
            prev_time = now

            # ── Update dashboard stats ─────────────────────────────
            _live_stats["fps"] = round(fps, 1)
            _live_stats["latency_ms"] = round(last_infer_ms, 1)
            _live_stats["detections"] = len(cached_boxes)
            _live_stats["highest_confidence"] = round(
                max([float(s) for s in cached_scores] + [0.0]), 3
            )
            _live_stats["last_active"] = now

            # ── Annotate frame ─────────────────────────────────────
            if len(cached_boxes) > 0:
                annotated = draw_detections(
                    frame, cached_boxes, cached_scores,
                    cached_class_ids, fps=fps
                )
            else:
                annotated = frame.copy()
                cv2.putText(annotated, "No Ball Detected", (20, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255),
                            2, cv2.LINE_AA)
                cv2.putText(annotated, f"FPS: {fps:.1f}", (15, 35),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0),
                            2, cv2.LINE_AA)

            # ── Yield MJPEG chunk ──────────────────────────────────
            ret, buffer = cv2.imencode('.jpg', annotated)
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n'
                       + buffer.tobytes() + b'\r\n')
                       
            # Sleep slightly to prevent high CPU usage if camera read is very fast
            time.sleep(0.005)

    except GeneratorExit:
        logger.info(">>> STREAMING: GeneratorExit — client disconnected.")
    except Exception as e:
        logger.error(f">>> STREAMING: Frame generator crashed: {e}")
    finally:
        logger.info(">>> STREAMING: Stopping Frame Generator...")
        _live_stats["active"] = False
        infer_worker.stop()
        cam_manager.stop()
        _live_stats["fps"] = 0.0
        _live_stats["latency_ms"] = 0.0
        _live_stats["detections"] = 0
        _live_stats["highest_confidence"] = 0.0
        logger.info(">>> STREAMING: Generator exited. Camera released. Cleanup complete.")

@app.get("/api/detect/live")
async def video_feed():
    # Stream Stealing: If a stream is already running (e.g. from a page refresh
    # or an unclosed connection), forcefully signal it to stop and release the camera.
    if _live_stats.get("active", False):
        logger.warning("Existing camera stream found. Forcing termination...")
        _live_stats["active"] = False
        cam_manager.stop()
        import asyncio
        await asyncio.sleep(0.5)  # Give the old generator time to fully clean up

    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.post("/api/detect/live/stop")
async def stop_feed():
    """Explicit stop endpoint — called by frontend Stop button for reliable cleanup."""
    logger.info(">>> /api/detect/live/stop called by client.")
    _live_stats["active"] = False
    cam_manager.stop()
    return JSONResponse({"status": "stopped"})

@app.get("/api/detect/live_stats")
async def get_live_stats():
    global _live_stats
    _live_stats["last_polled"] = time.time()

    if _live_stats.get("active", False):
        last_active = _live_stats.get("last_active", 0)
        # Watchdog: Kill if no frame activity for 10 seconds (generous for camera warm-up)
        if last_active > 0 and (time.time() - last_active) > 10.0:
            logger.warning("Watchdog: Stream frozen for >10s. Forcing CameraManager stop.")
            _live_stats["active"] = False
            cam_manager.stop()

    return JSONResponse(_live_stats)
