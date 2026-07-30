"""
performance.py — Performance Monitoring Utility
===============================================

Collects rolling metrics for the vision pipeline without
mixing concerns into the Tracker service.
"""

import time
from collections import deque
import statistics


class PerformanceMonitor:
    """Tracks latency, throughput, and errors using rolling averages."""
    
    def __init__(self, window_size: int = 100):
        self._start_time = time.perf_counter()
        
        # Rolling windows for latencies (in milliseconds)
        self._camera_latencies = deque(maxlen=window_size)
        self._detection_latencies = deque(maxlen=window_size)
        self._estimation_latencies = deque(maxlen=window_size)
        self._total_latencies = deque(maxlen=window_size)
        
        # Counters
        self._frames_processed = 0
        self._dropped_frames = 0
        
        # We track recent frame times to compute a true rolling FPS
        self._frame_times = deque(maxlen=window_size)

    def record_success(
        self, 
        camera_ms: float, 
        detection_ms: float, 
        estimation_ms: float, 
        total_ms: float
    ):
        """Records a successfully processed frame."""
        self._camera_latencies.append(camera_ms)
        self._detection_latencies.append(detection_ms)
        self._estimation_latencies.append(estimation_ms)
        self._total_latencies.append(total_ms)
        
        self._frame_times.append(time.perf_counter())
        self._frames_processed += 1

    def record_drop(self):
        """Records a dropped frame (e.g., no face, or error)."""
        self._dropped_frames += 1

    def get_fps(self) -> float:
        """Calculates FPS over the rolling window."""
        if len(self._frame_times) < 2:
            return 0.0
        duration = self._frame_times[-1] - self._frame_times[0]
        if duration <= 0:
            return 0.0
        return len(self._frame_times) / duration

    def _avg(self, d: deque) -> float:
        if not d:
            return 0.0
        return statistics.mean(d)

    def get_metrics(self) -> dict:
        """Returns the aggregated performance data."""
        return {
            "fps": round(self.get_fps(), 1),
            "camera_latency_ms": round(self._avg(self._camera_latencies), 2),
            "detection_latency_ms": round(self._avg(self._detection_latencies), 2),
            "estimation_latency_ms": round(self._avg(self._estimation_latencies), 2),
            "total_pipeline_latency_ms": round(self._avg(self._total_latencies), 2),
            "dropped_frames": self._dropped_frames,
            "frames_processed": self._frames_processed,
            "uptime_seconds": round(time.perf_counter() - self._start_time, 1)
        }
