"""FastAPI Application Factory"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, estimate, calibration, preview, metrics, frontend, static
from app.services.camera import camera_service
from app.services.detector import detector_service
from app.api.dependencies import tracker_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle hooks.
    Starts the hardware and tracker before accepting requests,
    and cleanly stops them on shutdown.
    """
    # -- Startup --
    camera_service.start()
    detector_service.start()
    tracker_service.start()
    yield
    # -- Shutdown --
    tracker_service.stop()
    detector_service.stop()
    camera_service.stop()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Monocular Face Distance Estimator API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api_router = APIRouter()
    api_router.include_router(frontend.router)
    api_router.include_router(static.router)
    api_router.include_router(health.router)
    api_router.include_router(estimate.router)
    api_router.include_router(calibration.router)
    api_router.include_router(preview.router)
    api_router.include_router(metrics.router)

    app.include_router(api_router)
    return app

app = create_app()
