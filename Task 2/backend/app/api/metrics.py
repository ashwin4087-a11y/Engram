"""Metrics and Health API"""
from fastapi import APIRouter, Depends
from app.models.api import ApiResponse
from app.models.performance import PerformanceReport
from app.api.dependencies import get_tracker_service, get_calibration_service
from app.services.tracker import TrackerService
from app.services.calibration import CalibrationService
from app.exceptions.calibration import CalibrationError

router = APIRouter(tags=["Metrics"])

@router.get(
    "/metrics",
    response_model=ApiResponse[PerformanceReport],
    summary="Get pipeline performance and health report",
)
async def get_metrics(
    tracker: TrackerService = Depends(get_tracker_service),
    calibration_svc: CalibrationService = Depends(get_calibration_service)
) -> ApiResponse[PerformanceReport]:
    
    # Get raw metrics from tracker
    metrics = tracker._perf_monitor.get_metrics()
    
    # Get tracker status
    state = tracker.get_latest_state()
    
    # Check calibration status
    try:
        calibration_svc.get_calibration()
        cal_status = "READY"
    except CalibrationError:
        cal_status = "NOT CALIBRATED"
        
    report = PerformanceReport(
        status=state.status,
        fps=metrics["fps"],
        camera_latency_ms=metrics["camera_latency_ms"],
        detection_latency_ms=metrics["detection_latency_ms"],
        estimation_latency_ms=metrics["estimation_latency_ms"],
        total_pipeline_latency_ms=metrics["total_pipeline_latency_ms"],
        dropped_frames=metrics["dropped_frames"],
        frames_processed=metrics["frames_processed"],
        uptime_seconds=metrics["uptime_seconds"],
        camera="CONNECTED" if state.status != "NO_CAMERA" else "DISCONNECTED",
        detector="ACTIVE",
        calibration=cal_status
    )
    
    return ApiResponse[PerformanceReport](
        success=True,
        data=report,
        message="Metrics retrieved successfully."
    )
