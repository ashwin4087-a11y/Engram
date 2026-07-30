"""
estimate.py — Estimation Endpoints
==================================

Routes for distance and angle estimation.
"""

from fastapi import APIRouter

from app.models.api import ApiResponse
from app.models.estimation import EstimateData

router = APIRouter(tags=["Estimation"])


@router.get(
    "/estimate",
    response_model=ApiResponse[EstimateData],
    summary="Get distance and angle estimate",
)
async def get_estimate() -> ApiResponse[EstimateData]:
    """
    Returns the current distance and angle estimate.
    (Placeholder for Module 8)
    """
    # TODO: Call TrackerService
    return ApiResponse[EstimateData](
        success=False,
        message="Not implemented yet",
    )
