"""Calibration Endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from app.models.api import ApiResponse
from app.models.calibration import CalibrationRequest, CalibrationData, CalibrationStatusData
from app.exceptions.calibration import CalibrationError
from app.api.dependencies import get_calibration_service
from app.services.calibration import CalibrationService

router = APIRouter(tags=["Calibration"])

@router.get(
    "/calibration",
    response_model=ApiResponse[CalibrationStatusData],
    summary="Get calibration status"
)
async def get_calibration_status(
    service: CalibrationService = Depends(get_calibration_service)
) -> ApiResponse[CalibrationStatusData]:
    try:
        data = service.get_calibration()
        return ApiResponse[CalibrationStatusData](
            success=True,
            data=CalibrationStatusData(calibrated=True, data=data)
        )
    except CalibrationError:
        return ApiResponse[CalibrationStatusData](
            success=True,
            data=CalibrationStatusData(calibrated=False, data=None)
        )

@router.post(
    "/calibrate",
    response_model=ApiResponse[CalibrationData],
    summary="Run calibration session"
)
async def calibrate(
    request: CalibrationRequest,
    service: CalibrationService = Depends(get_calibration_service)
) -> ApiResponse[CalibrationData]:
    try:
        data = service.calibrate(
            known_distance=request.known_distance,
            known_face_width=request.known_face_width
        )
        return ApiResponse[CalibrationData](
            success=True,
            data=data,
            message=f"Calibrated successfully. Standard deviation: {data.std_dev:.2f}px"
        )
    except CalibrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
@router.delete(
    "/calibration",
    response_model=ApiResponse[None],
    summary="Reset calibration"
)
async def reset_calibration(
    service: CalibrationService = Depends(get_calibration_service)
) -> ApiResponse[None]:
    service.reset()
    return ApiResponse[None](success=True, message="Calibration reset.")
