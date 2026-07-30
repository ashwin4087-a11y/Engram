"""
dependencies.py — FastAPI Dependency Injection
==============================================

Provides singleton instances of services to route handlers.
"""

from app.core.settings import settings
from app.services.camera import camera_service
from app.services.detector import detector_service
from app.services.calibration_storage import CalibrationStorage
from app.services.calibration import CalibrationService


from app.services.tracker import TrackerService

# Initialize singletons for services that don't need lifecycle hooks,
# or compose them here.

calibration_storage = CalibrationStorage(filepath=settings.CALIBRATION_FILE)

calibration_service_singleton = CalibrationService(
    camera=camera_service,
    detector=detector_service,
    storage=calibration_storage,
)

tracker_service = TrackerService(
    camera=camera_service,
    detector=detector_service,
    calibration_storage=calibration_storage,
)

def get_calibration_service() -> CalibrationService:
    """Dependency provider for CalibrationService."""
    return calibration_service_singleton

def get_tracker_service() -> TrackerService:
    """Dependency provider for TrackerService."""
    return tracker_service
