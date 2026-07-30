"""
settings.py — Single Source of Configuration
==============================================

All configurable values live here.  No other module should read
os.environ or hardcode numeric / string literals that represent
tuneable thresholds or defaults.

Usage:
    from app.core.settings import settings

    settings.CAMERA_INDEX
    settings.EMA_ALPHA
    settings.DEBUG

Paths (derived from project layout, not env-configurable):
    from app.core.settings import DATA_DIR, CALIBRATION_FILE, LOG_FILE
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# Derived paths (computed from project structure, not env vars)
# ---------------------------------------------------------------------------

_CORE_DIR: Path = Path(__file__).resolve().parent       # app/core/
_APP_DIR: Path = _CORE_DIR.parent                       # app/
PROJECT_ROOT: Path = _APP_DIR.parent                    # Task 2/

DATA_DIR: Path = _APP_DIR / "data"
CALIBRATION_FILE: Path = DATA_DIR / "focal_length.json"
LOG_FILE: Path = DATA_DIR / "estimation_log.csv"


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class Settings(BaseSettings):
    """
    Application-wide settings loaded from environment variables / .env.

    Grouped by domain for readability.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -- Server ---------------------------------------------------------------
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # -- Camera ---------------------------------------------------------------
    CAMERA_INDEX: int = 0
    CAMERA_WIDTH: int = 640
    CAMERA_HEIGHT: int = 480

    # -- Face geometry --------------------------------------------------------
    DEFAULT_FACE_WIDTH: float = 0.15          # metres (ear-to-ear average)

    # -- Detection thresholds -------------------------------------------------
    MAX_FACES: int = 1
    MIN_CONFIDENCE: float = 0.5

    # -- Smoothing / filtering ------------------------------------------------
    EMA_ALPHA: float = 0.3                    # 0 < α ≤ 1

    # -- MediaPipe Face Mesh landmark indices ---------------------------------
    LANDMARK_RIGHT_CHEEK: int = 234
    LANDMARK_LEFT_CHEEK: int = 454

    # -- Estimator heuristics -------------------------------------------------
    MIN_RELIABLE_FACE_PX: float = 20.0
    MAX_RELIABLE_FACE_PX: float = 500.0
    MIN_RELIABLE_DISTANCE: float = 0.2        # metres
    MAX_RELIABLE_DISTANCE: float = 5.0        # metres

    # -- JPEG encoding (for /frame endpoint) ----------------------------------
    JPEG_QUALITY: int = 85


# Module-level singleton — import this, not the class.
settings = Settings()
