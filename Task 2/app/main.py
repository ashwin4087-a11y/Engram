"""
main.py — FastAPI Application Factory
=======================================

Creates and configures the FastAPI application instance.
"""

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, estimate, calibration


def create_app() -> FastAPI:
    """
    Application factory.
    Creates and configures the FastAPI instance.
    """
    app = FastAPI(
        title="Monocular Face Distance Estimator API",
        description=(
            "Estimates a person's distance from the camera and horizontal "
            "viewing angle using a single webcam and the pinhole camera model."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Tighten in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Construct API Router
    api_router = APIRouter()
    api_router.include_router(health.router)
    api_router.include_router(estimate.router)
    api_router.include_router(calibration.router)

    # Register Router
    app.include_router(api_router)

    return app


# Create the global app instance for Uvicorn
app = create_app()
