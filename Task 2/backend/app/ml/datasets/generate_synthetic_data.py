"""
generate_synthetic_data.py — Synthetic Posture Dataset Generator
=================================================================

Generates a labelled CSV dataset for initial model training when no
real-world recording data is available.

IMPORTANT — this is a BOOTSTRAP tool only.
Replace or augment with real capture data as soon as possible.
Real data is always more accurate than synthetic.

Usage
-----
    python -m app.ml.datasets.generate_synthetic_data \\
        --samples 5000 \\
        --out     app/ml/datasets/posture_data.csv \\
        [--seed 42]

Output CSV schema
-----------------
head_yaw, head_pitch, head_roll,
eye_level_ratio, eye_horizontal_diff, nose_eye_dist,
face_aspect_ratio, face_size_ratio, chin_forehead_ratio,
left_eye_aspect, right_eye_aspect, mouth_openness,
label

Generation strategy
-------------------
Each posture class has characteristic distributions for the key features.
Gaussian noise is added to each sample so the classifier must learn
boundaries rather than memorise exact values.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from app.ml.models.posture_labels import POSTURE_LABELS, PostureClass
from app.ml.preprocessing.feature_extractor import FEATURE_NAMES

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Per-class feature distributions  (mean, std) for each of the 12 features
# ---------------------------------------------------------------------------
# Layout: [yaw, pitch, roll, shoulder_angle, neck_angle, torso_inclination, spine_orientation,
#          face_sz, inter_eye_dist, eye_level, eye_diff, nose_eye, face_ar,
#          chin_fh, l_ear, r_ear, mouth]

_DISTRIBUTIONS: Dict[PostureClass, Tuple[list, list]] = {
    PostureClass.GOOD_POSTURE: (
        [ 0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, 0.12, 0.15, 0.45, 0.01, 0.08, 0.75, 1.0, 0.28, 0.28, 0.10],
        [ 5.0,  5.0,  3.0,  3.0,  3.0,  3.0,  2.0, 0.02, 0.01, 0.03, 0.01, 0.01, 0.05, 0.05, 0.04, 0.04, 0.03],
    ),
    PostureClass.LEANING_FORWARD: (
        [ 0.0,  3.0,  0.0,  0.0,  5.0, 15.0,  0.0, 0.30, 0.18, 0.45, 0.01, 0.08, 0.75, 1.0, 0.28, 0.28, 0.10],
        [ 6.0,  6.0,  4.0,  3.0,  5.0,  5.0,  2.0, 0.05, 0.02, 0.03, 0.01, 0.02, 0.06, 0.05, 0.04, 0.04, 0.03],
    ),
    PostureClass.LEANING_BACKWARD: (
        [ 0.0, -3.0,  0.0,  0.0, -5.0,-10.0,  0.0, 0.05, 0.10, 0.45, 0.01, 0.08, 0.75, 1.0, 0.28, 0.28, 0.10],
        [ 6.0,  6.0,  4.0,  3.0,  5.0,  5.0,  2.0, 0.02, 0.01, 0.03, 0.01, 0.02, 0.06, 0.05, 0.04, 0.04, 0.03],
    ),
    PostureClass.LOOKING_DOWN: (
        [ 0.0,-22.0,  0.0,  0.0,-20.0,  5.0,  0.0, 0.12, 0.15, 0.55, 0.01, 0.12, 0.72, 1.1, 0.20, 0.20, 0.10],
        [ 6.0,  6.0,  3.0,  3.0,  5.0,  4.0,  2.0, 0.02, 0.01, 0.04, 0.01, 0.02, 0.05, 0.05, 0.04, 0.04, 0.03],
    ),
    PostureClass.LOOKING_UP: (
        [ 0.0, 22.0,  0.0,  0.0, 20.0, -2.0,  0.0, 0.12, 0.15, 0.35, 0.01, 0.05, 0.78, 0.9, 0.32, 0.32, 0.12],
        [ 6.0,  6.0,  3.0,  3.0,  5.0,  4.0,  2.0, 0.02, 0.01, 0.04, 0.01, 0.01, 0.05, 0.05, 0.04, 0.04, 0.03],
    ),
    PostureClass.HEAD_TILT_LEFT: (
        [18.0,  0.0, 18.0, 15.0, 10.0,  0.0, 10.0, 0.12, 0.15, 0.45, 0.05, 0.08, 0.75, 1.0, 0.30, 0.26, 0.10],
        [ 5.0,  5.0,  5.0,  4.0,  4.0,  3.0,  3.0, 0.02, 0.01, 0.03, 0.02, 0.01, 0.05, 0.05, 0.04, 0.04, 0.03],
    ),
    PostureClass.HEAD_TILT_RIGHT: (
        [-18.0, 0.0,-18.0,-15.0,-10.0,  0.0,-10.0, 0.12, 0.15, 0.45, 0.05, 0.08, 0.75, 1.0, 0.26, 0.30, 0.10],
        [  5.0, 5.0,  5.0,  4.0,  4.0,  3.0,  3.0, 0.02, 0.01, 0.03, 0.02, 0.01, 0.05, 0.05, 0.04, 0.04, 0.03],
    ),
}

def generate_dataset(
    n_samples: int = 5000,
    seed: int = 42,
    balance: bool = True,
) -> pd.DataFrame:
    """
    Generate a synthetic posture dataset.

    Parameters
    ----------
    n_samples : Total number of rows (split equally across classes by default).
    seed      : RNG seed for reproducibility.
    balance   : If True, each class gets n_samples // NUM_CLASSES rows.

    Returns
    -------
    pd.DataFrame with feature columns + 'label' string column.
    """
    rng = np.random.default_rng(seed)

    classes = list(_DISTRIBUTIONS.keys())
    n_classes = len(classes)
    per_class = n_samples // n_classes if balance else n_samples // n_classes

    rows = []
    for cls in classes:
        means, stds = _DISTRIBUTIONS[cls]
        means = np.array(means, dtype=np.float32)
        stds  = np.array(stds,  dtype=np.float32)

        samples = rng.normal(loc=means, scale=stds, size=(per_class, len(means)))

        # Clip to physically plausible ranges
        samples[:, 0]  = np.clip(samples[:, 0],  -90.0, 90.0)   # yaw
        samples[:, 1]  = np.clip(samples[:, 1],  -45.0, 45.0)   # pitch
        samples[:, 2]  = np.clip(samples[:, 2],  -45.0, 45.0)   # roll
        samples[:, 3]  = np.clip(samples[:, 3],  -45.0, 45.0)   # shoulder_angle
        samples[:, 4]  = np.clip(samples[:, 4],  -45.0, 45.0)   # neck_angle
        samples[:, 5]  = np.clip(samples[:, 5],  -45.0, 45.0)   # torso_inclination
        samples[:, 6]  = np.clip(samples[:, 6],  -45.0, 45.0)   # spine_orientation
        samples[:, 7]  = np.clip(samples[:, 7],   0.01, 0.6)    # face_size
        samples[:, 8]  = np.clip(samples[:, 8],   0.05, 0.3)    # inter_eye_dist
        samples[:, 9]  = np.clip(samples[:, 9],   0.1,  0.9)    # eye_level
        samples[:, 10] = np.clip(samples[:, 10],  0.0,  0.2)    # eye_diff
        samples[:, 11] = np.clip(samples[:, 11],  0.0,  0.3)    # nose_eye
        samples[:, 12] = np.clip(samples[:, 12],  0.4,  1.5)    # face_ar
        samples[:, 13] = np.clip(samples[:, 13],  0.5,  1.5)    # chin_fh
        samples[:, 14] = np.clip(samples[:, 14],  0.05, 0.6)    # l_ear
        samples[:, 15] = np.clip(samples[:, 15],  0.05, 0.6)    # r_ear
        samples[:, 16] = np.clip(samples[:, 16],  0.0,  0.8)    # mouth

        label_str = POSTURE_LABELS[int(cls)]
        df_cls = pd.DataFrame(samples, columns=FEATURE_NAMES)
        df_cls["label"] = label_str
        rows.append(df_cls)

    df = pd.concat(rows, ignore_index=True)
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    log.info("Generated %d synthetic samples across %d classes.", len(df), n_classes)
    return df


def _cli() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    parser = argparse.ArgumentParser(description="Generate synthetic posture training data.")
    parser.add_argument("--samples", type=int, default=5000)
    parser.add_argument("--out",     default="app/ml/datasets/posture_data.csv")
    parser.add_argument("--seed",    type=int, default=42)
    args = parser.parse_args()

    df = generate_dataset(n_samples=args.samples, seed=args.seed)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"✓ Saved {len(df)} rows → {out}")
    print(df["label"].value_counts().to_string())


if __name__ == "__main__":
    _cli()
