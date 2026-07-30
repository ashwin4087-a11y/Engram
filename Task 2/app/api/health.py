"""
health.py — Health Endpoints
============================

Health check routes.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.models.api import ApiResponse

router = APIRouter()


class HealthData(BaseModel):
    """Payload for the root health-check endpoint."""
    status: str


@router.get(
    "/health",
    response_model=ApiResponse[HealthData],
    tags=["Health"],
    summary="Health check",
)
async def health_check() -> ApiResponse[HealthData]:
    """
    Lightweight health-check endpoint.
    """
    return ApiResponse[HealthData](
        success=True,
        data=HealthData(status="running"),
        message="Monocular Face Distance Estimator API",
    )
