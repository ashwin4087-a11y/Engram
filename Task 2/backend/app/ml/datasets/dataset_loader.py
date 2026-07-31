"""
dataset_loader.py — CSV Dataset Loader for Posture Classification
=================================================================

Expected CSV schema
-------------------
One row per sample.  Columns can be in any order.

Required columns
~~~~~~~~~~~~~~~~
  label   : str  — one of the POSTURE_LABELS strings
                   OR an integer matching PostureClass values.

Feature columns (12 total, in any order)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  head_yaw, head_pitch, head_roll,
  eye_level_ratio, eye_horizontal_diff, nose_eye_dist,
  face_aspect_ratio, face_size_ratio, chin_forehead_ratio,
  left_eye_aspect, right_eye_aspect, mouth_openness

Optional metadata columns (ignored during training)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  subject_id, session_id, timestamp, frame_id

Usage
-----
    from app.ml.datasets.dataset_loader import load_dataset
    X, y = load_dataset("path/to/posture_data.csv")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

from app.ml.models.posture_labels import POSTURE_LABELS, PostureClass
from app.ml.preprocessing.feature_extractor import FEATURE_NAMES

log = logging.getLogger(__name__)

# Reverse map: "LEANING_FORWARD" → 1
_LABEL_TO_INT = {v: k for k, v in POSTURE_LABELS.items()}

# Metadata columns that are NOT features
_META_COLS = {"label", "subject_id", "session_id", "timestamp", "frame_id"}


def load_dataset(
    csv_path: str | Path,
    drop_na: bool = True,
    shuffle: bool = True,
    random_state: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load and validate a posture CSV dataset.

    Parameters
    ----------
    csv_path     : Path to the CSV file.
    drop_na      : Drop rows with any NaN in feature columns.
    shuffle      : Shuffle rows before returning.
    random_state : Seed for reproducibility.

    Returns
    -------
    X : np.ndarray, shape (N, 12), dtype float32
    y : np.ndarray, shape (N,),   dtype int32
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path)
    log.info("Loaded %d rows from %s", len(df), path)

    # ── Validate label column ──────────────────────────────────────────
    if "label" not in df.columns:
        raise ValueError("CSV must contain a 'label' column.")

    # Normalise string labels
    def _parse_label(val) -> int:
        if isinstance(val, (int, np.integer)):
            return int(val)
        s = str(val).strip().upper()
        if s in _LABEL_TO_INT:
            return _LABEL_TO_INT[s]
        raise ValueError(f"Unknown label: '{val}'. Valid labels: {list(_LABEL_TO_INT)}")

    df["_label_int"] = df["label"].apply(_parse_label)

    # ── Validate / select feature columns ─────────────────────────────
    missing = [f for f in FEATURE_NAMES if f not in df.columns]
    if missing:
        raise ValueError(
            f"CSV is missing required feature columns: {missing}\n"
            f"Required: {FEATURE_NAMES}"
        )

    X_df = df[FEATURE_NAMES].copy()

    if drop_na:
        before = len(X_df)
        mask   = X_df.notna().all(axis=1)
        X_df   = X_df[mask]
        df     = df[mask]
        dropped = before - len(X_df)
        if dropped:
            log.warning("Dropped %d rows with NaN values.", dropped)

    X = X_df.values.astype(np.float32)
    y = df["_label_int"].values.astype(np.int32)

    # ── Shuffle ────────────────────────────────────────────────────────
    if shuffle:
        rng  = np.random.default_rng(random_state)
        idx  = rng.permutation(len(X))
        X, y = X[idx], y[idx]

    log.info(
        "Dataset ready: %d samples, %d features, %d classes",
        len(X), X.shape[1], len(np.unique(y))
    )
    return X, y


def describe_dataset(X: np.ndarray, y: np.ndarray) -> str:
    """Return a human-readable summary of a loaded dataset."""
    lines = [
        f"Samples  : {len(X)}",
        f"Features : {X.shape[1]}",
        "Class distribution:",
    ]
    unique, counts = np.unique(y, return_counts=True)
    for cls_id, cnt in zip(unique, counts):
        label = POSTURE_LABELS.get(int(cls_id), f"class_{cls_id}")
        lines.append(f"  {label:<22} {cnt:>5} ({cnt/len(y)*100:.1f}%)")
    return "\n".join(lines)
