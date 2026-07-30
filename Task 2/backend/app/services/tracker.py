"""
tracker.py — Tracker Service Orchestrator
=========================================

The heart of the application. Runs a continuous background thread
to pull frames, detect faces, apply EMA smoothing on inputs,
estimate distance/angle, and apply EMA smoothing on outputs.
Caches the latest state for instant API retrieval.
"""

import time
import threading
from datetime import datetime, timezone
import copy

from app.core.settings import settings
from app.exceptions.camera import CameraError
from app.exceptions.detector import FaceDetectionError
from app.exceptions.estimation import EstimationError

from app.services.camera import CameraService
from app.services.detector import FaceDetectionService
from app.services.calibration_storage import CalibrationStorage
from app.services.estimator import EstimatorService

from app.utils.smoothing import ExponentialMovingAverage
from app.utils.performance import PerformanceMonitor
from app.models.tracker import TrackerState, TrackerStatus


class TrackerService:
    """
    Orchestrates the continuous CV pipeline in a background thread.
    Caches the latest state in a thread-safe manner.
    """

    def __init__(
        self,
        camera: CameraService,
        detector: FaceDetectionService,
        calibration_storage: CalibrationStorage
    ):
        self._camera = camera
        self._detector = detector
        self._cal_storage = calibration_storage
        
        # Smoothing Filters
        alpha = settings.EMA_ALPHA
        self._width_filter = ExponentialMovingAverage(alpha)
        self._x_filter = ExponentialMovingAverage(alpha)
        self._distance_filter = ExponentialMovingAverage(alpha)
        self._angle_filter = ExponentialMovingAverage(alpha)

        # Performance Monitor
        self._perf_monitor = PerformanceMonitor(window_size=150)

        # Threading & State
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        
        self._state = TrackerState(
            status=TrackerStatus.INITIALIZING,
            timestamp=datetime.now(timezone.utc).isoformat(),
            fps=0.0
        )

    def start(self):
        """Starts the background tracking loop."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True, name="TrackerLoop")
            self._thread.start()

    def stop(self):
        """Stops the tracking loop."""
        with self._lock:
            self._running = False
            
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def get_latest_state(self) -> TrackerState:
        """Thread-safe read of the current tracker state."""
        with self._lock:
            # Return a shallow copy of the state dataclass to avoid race conditions during read
            return copy.copy(self._state)

    def _update_state(self, **kwargs):
        """Helper to thread-safely update fields on the current state."""
        with self._lock:
            for k, v in kwargs.items():
                setattr(self._state, k, v)
            self._state.timestamp = datetime.now(timezone.utc).isoformat()

    def _reset_filters(self):
        """Resets all EMA filters (e.g., when face is lost)."""
        self._width_filter.reset()
        self._x_filter.reset()
        self._distance_filter.reset()
        self._angle_filter.reset()

    def _run_loop(self):
        """Continuous pipeline loop running in a background thread."""
        last_fps_time = time.perf_counter()
        
        while self._running:
            try:
                loop_start = time.perf_counter()
                
                # 1. Capture
                t0 = time.perf_counter()
                try:
                    frame_data = self._camera.get_frame()
                except CameraError:
                    self._update_state(status=TrackerStatus.NO_CAMERA, frame=None, detection=None, estimate=None)
                    self._perf_monitor.record_drop()
                    time.sleep(0.1)
                    continue
                camera_ms = (time.perf_counter() - t0) * 1000

                raw_frame = frame_data.frame
                
                # 2. Detect
                t1 = time.perf_counter()
                try:
                    det_result = self._detector.detect(raw_frame)
                except FaceDetectionError as e:
                    self._update_state(status=TrackerStatus.ERROR, error_message=str(e), frame=raw_frame, detection=None, estimate=None)
                    self._perf_monitor.record_drop()
                    time.sleep(0.03)
                    continue
                detection_ms = (time.perf_counter() - t1) * 1000

                if not det_result.detected or not det_result.detection:
                    self._reset_filters()
                    self._update_state(status=TrackerStatus.NO_FACE, frame=raw_frame, detection=None, estimate=None)
                    self._perf_monitor.record_drop()
                    time.sleep(0.01)
                    continue

                raw_det = det_result.detection
                
                # 3. Estimate & Smooth
                t2 = time.perf_counter()
                smoothed_width = self._width_filter.update(raw_det.face_width_px)
                smoothed_cx = self._x_filter.update(raw_det.center_x)
                
                smoothed_det = raw_det.model_copy(update={
                    "face_width_px": smoothed_width,
                    "center_x": smoothed_cx
                })

                calibration = self._cal_storage.load()
                if not calibration:
                    self._update_state(status=TrackerStatus.NOT_CALIBRATED, frame=raw_frame, detection=smoothed_det, estimate=None)
                    self._perf_monitor.record_drop()
                    time.sleep(0.01)
                    continue

                resolution = (self._camera._width, self._camera._height)
                try:
                    raw_est = EstimatorService.estimate(
                        detection=smoothed_det,
                        calibration=calibration,
                        image_resolution=resolution
                    )
                except EstimationError as e:
                    self._update_state(status=TrackerStatus.ERROR, error_message=str(e), frame=raw_frame, detection=smoothed_det, estimate=None)
                    self._perf_monitor.record_drop()
                    time.sleep(0.01)
                    continue

                smoothed_dist = self._distance_filter.update(raw_est.distance)
                smoothed_angle = self._angle_filter.update(raw_est.angle)
                
                final_est = raw_est.model_copy(update={
                    "distance": smoothed_dist,
                    "angle": smoothed_angle
                })
                estimation_ms = (time.perf_counter() - t2) * 1000
                total_ms = (time.perf_counter() - loop_start) * 1000
                
                # Record Success Metrics
                self._perf_monitor.record_success(camera_ms, detection_ms, estimation_ms, total_ms)

                # 4. Update Cache & FPS
                current_time = time.perf_counter()
                fps = 1.0 / (current_time - last_fps_time) if (current_time - last_fps_time) > 0 else 0
                last_fps_time = current_time
                
                self._update_state(
                    status=TrackerStatus.RUNNING,
                    frame=raw_frame,
                    detection=smoothed_det,
                    estimate=final_est,
                    fps=fps,
                    error_message=None
                )
                
                time.sleep(0.005)

            except Exception as e:
                self._update_state(status=TrackerStatus.ERROR, error_message=f"Unhandled loop error: {e}")
                self._perf_monitor.record_drop()
                time.sleep(0.1)
