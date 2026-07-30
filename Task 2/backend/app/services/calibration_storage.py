"""
calibration_storage.py — Calibration Persistence
================================================

Handles saving and loading of the calibration JSON file.
Separated from the computation logic.
"""

import json
from pathlib import Path
from typing import Optional

from app.models.calibration import CalibrationData
from app.exceptions.calibration import CalibrationError


class CalibrationStorage:
    """Handles JSON persistence for camera calibration data."""
    
    def __init__(self, filepath: Path):
        self._filepath = filepath

    def save(self, data: CalibrationData) -> None:
        """Saves CalibrationData to disk."""
        try:
            # Ensure directory exists
            self._filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self._filepath, 'w', encoding='utf-8') as f:
                f.write(data.model_dump_json(indent=2))
        except Exception as e:
            raise CalibrationError(f"Failed to save calibration data: {e}")

    def load(self) -> Optional[CalibrationData]:
        """Loads CalibrationData from disk if it exists."""
        if not self._filepath.exists():
            return None
            
        try:
            with open(self._filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return CalibrationData.model_validate(data)
        except Exception as e:
            raise CalibrationError(f"Failed to load calibration data: {e}")

    def delete(self) -> None:
        """Deletes the calibration file."""
        try:
            if self._filepath.exists():
                self._filepath.unlink()
        except Exception as e:
            raise CalibrationError(f"Failed to delete calibration data: {e}")
