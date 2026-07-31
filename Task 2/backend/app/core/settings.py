"""Single Source of Configuration"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_CORE_DIR: Path = Path(__file__).resolve().parent
_APP_DIR: Path = _CORE_DIR.parent
PROJECT_ROOT: Path = _APP_DIR.parent

DATA_DIR: Path = _APP_DIR / "data"
CALIBRATION_FILE: Path = DATA_DIR / "focal_length.json"
LOG_FILE: Path = DATA_DIR / "estimation_log.csv"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    DATA_DIR: Path = DATA_DIR
    CALIBRATION_FILE: Path = CALIBRATION_FILE
    LOG_FILE: Path = LOG_FILE

    CAMERA_INDEX: int = 0
    CAMERA_WIDTH: int = 640
    CAMERA_HEIGHT: int = 480

    DEFAULT_FACE_WIDTH: float = 0.15
    MAX_FACES: int = 1
    MIN_CONFIDENCE: float = 0.5
    EMA_ALPHA: float = 0.3

    LEFT_FACE_EDGE: int = 454
    RIGHT_FACE_EDGE: int = 234

    MIN_RELIABLE_FACE_PX: float = 20.0
    MAX_RELIABLE_FACE_PX: float = 500.0
    MIN_RELIABLE_DISTANCE: float = 0.2
    MAX_RELIABLE_DISTANCE: float = 5.0

    JPEG_QUALITY: int = 85

settings = Settings()
