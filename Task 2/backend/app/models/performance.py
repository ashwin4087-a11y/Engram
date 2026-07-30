"""Performance and Health Models"""
from pydantic import BaseModel
from app.models.tracker import TrackerStatus

class PerformanceReport(BaseModel):
    """Detailed performance and health metrics for the backend pipeline."""
    status: TrackerStatus
    fps: float
    camera_latency_ms: float
    detection_latency_ms: float
    estimation_latency_ms: float
    total_pipeline_latency_ms: float
    dropped_frames: int
    frames_processed: int
    uptime_seconds: float
    
    # System Status
    camera: str
    detector: str
    calibration: str
