"""
model_info.py — Utility helpers for model artefact management
=============================================================
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


_ARTEFACT_DIR = Path(__file__).parent.parent / "models" / "artefacts"


def artefact_exists(name: str = "posture_classifier.ubj") -> bool:
    """Return True if the named model artefact file exists."""
    return (_ARTEFACT_DIR / name).exists()


def load_training_report(name: str = "training_report.json") -> Optional[dict]:
    """Load and return the JSON training report, or None if not found."""
    path = _ARTEFACT_DIR / name
    if not path.exists():
        return None
    with open(path) as fh:
        return json.load(fh)


def artefact_dir() -> Path:
    """Return the Path to the model artefact directory."""
    return _ARTEFACT_DIR
