"""Health Endpoints"""
from fastapi import APIRouter
from pydantic import BaseModel
from app.models.api import ApiResponse

router = APIRouter()

class HealthData(BaseModel):
    status: str

@router.get(
    "/health",
    response_model=ApiResponse[HealthData],
    tags=["Health"],
    summary="Health check",
)
async def health_check() -> ApiResponse[HealthData]:
    return ApiResponse[HealthData](
        success=True,
        data=HealthData(status="running"),
        message="Monocular Face Distance Estimator API",
    )
