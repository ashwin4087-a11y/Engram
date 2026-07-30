"""Estimation Endpoints"""
from fastapi import APIRouter, Depends
from app.models.api import ApiResponse
from app.models.tracker import TrackerResponse
from app.api.dependencies import get_tracker_service
from app.services.tracker import TrackerService

router = APIRouter(tags=["Estimation"])

@router.get(
    "/estimate",
    response_model=ApiResponse[TrackerResponse],
    summary="Get latest distance and angle estimate",
    description="Returns the instant cached state of the background tracking pipeline."
)
async def get_estimate(
    tracker: TrackerService = Depends(get_tracker_service)
) -> ApiResponse[TrackerResponse]:
    
    state = tracker.get_latest_state()
    response_data = TrackerResponse.from_state(state)
    
    return ApiResponse[TrackerResponse](
        success=True,
        data=response_data,
        message="Tracker state retrieved."
    )
