"""
routes.py — API Route Handlers
================================

This file contains ONLY HTTP endpoint definitions.
No OpenCV.  No MediaPipe.  No mathematics.  No business logic.

Each handler:
    1. Receives the HTTP request
    2. Calls the appropriate service (injected via FastAPI Depends)
    3. Returns an ApiResponse envelope

Module 1 defines only the health endpoint.
Additional routes will be added as each module is built.
"""

from fastapi import APIRouter

from app.models.schemas import ApiResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@router.get(
    "/health",
    response_model=ApiResponse,
    tags=["Health"],
    summary="Health check",
)
async def health_check() -> ApiResponse:
    """
    Lightweight health-check endpoint.

    Returns a confirmation that the API is running.
    Useful for load balancers, monitoring, and frontend connectivity tests.
    """
    return ApiResponse(
        success=True,
        data={"status": "running"},
        message="Monocular Face Distance Estimator API",
    )
