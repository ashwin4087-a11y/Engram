"""
calibration.py — Calibration Endpoints
======================================

Routes for camera calibration.
"""

from fastapi import APIRouter

from app.models.api import ApiResponse
from app.models.calibration import CalibrationRequest, CalibrationData

router = APIRouter(tags=["Calibration"])


@router.post(
    "/calibrate",
    response_model=ApiResponse[CalibrationData],
    summary="Run calibration",
)
async def calibrate(request: CalibrationRequest) -> ApiResponse[CalibrationData]:
    """
    Run focal-length calibration with a known distance.
    (Placeholder for Module 8)
    """
    # TODO: Call CalibrationService
    return ApiResponse[CalibrationData](
        success=False,
        message="Not implemented yet",
    )
