"""
train.py — Posture Classifier Training Pipeline
================================================

Trains an XGBoost multi-class classifier on a posture CSV dataset and saves
the model artefact + feature scaler so the inference layer can load them.

Usage
-----
    python -m app.ml.training.train \\
        --data  path/to/posture_data.csv \\
        --out   app/ml/models/artefacts \\
        [--test-size 0.2] \\
        [--n-estimators 300] \\
        [--max-depth 6] \\
        [--seed 42]

Or as a library:
    from app.ml.training.train import train_and_save
    metrics = train_and_save("posture_data.csv")

Output files
------------
  <out>/posture_classifier.ubj   — XGBoost binary model
  <out>/feature_scaler.npy       — StandardScaler mean + std arrays
  <out>/training_report.json     — Accuracy, per-class F1, confusion matrix
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

import numpy as np

# Configure logging before anything else
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core training function
# ---------------------------------------------------------------------------

def train_and_save(
    csv_path: str,
    out_dir: str = "app/ml/models/artefacts",
    test_size: float = 0.20,
    n_estimators: int = 300,
    max_depth: int = 6,
    learning_rate: float = 0.1,
    subsample: float = 0.8,
    colsample_bytree: float = 0.8,
    seed: int = 42,
) -> dict:
    """
    End-to-end training and serialisation.

    Returns a metrics dictionary that is also saved as training_report.json.
    """
    # ── Imports (inside function to keep top-level safe when xgboost absent)
    try:
        import xgboost as xgb
    except ImportError:
        log.error(
            "xgboost is not installed.  Install it with:\n"
            "    pip install xgboost"
        )
        sys.exit(1)

    from sklearn.model_selection import train_test_split, StratifiedKFold
    from sklearn.metrics import (
        accuracy_score, classification_report, confusion_matrix
    )
    from sklearn.preprocessing import LabelEncoder

    from app.ml.datasets.dataset_loader import load_dataset, describe_dataset
    from app.ml.models.posture_labels import POSTURE_LABELS, CLASS_NAMES, NUM_CLASSES

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # ── 1. Load data ──────────────────────────────────────────────────────
    log.info("Loading dataset: %s", csv_path)
    X, y = load_dataset(csv_path, shuffle=True, random_state=seed)
    log.info("\n%s", describe_dataset(X, y))

    # ── 2. Feature scaling (StandardScaler — mean/std per feature) ────────
    scaler_mean = X.mean(axis=0)
    scaler_std  = X.std(axis=0) + 1e-8
    X_scaled    = (X - scaler_mean) / scaler_std
    log.info("Features scaled (StandardScaler).")

    # ── 3. Train / test split ─────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y,
        test_size=test_size,
        random_state=seed,
        stratify=y,
    )
    log.info(
        "Split: train=%d  test=%d  (test_size=%.0f%%)",
        len(X_train), len(X_test), test_size * 100
    )

    # ── 4. XGBoost training ───────────────────────────────────────────────
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dtest  = xgb.DMatrix(X_test,  label=y_test)

    params = {
        "objective":        "multi:softprob",
        "num_class":        NUM_CLASSES,
        "eval_metric":      ["mlogloss", "merror"],
        "max_depth":        max_depth,
        "learning_rate":    learning_rate,
        "n_estimators":     n_estimators,
        "subsample":        subsample,
        "colsample_bytree": colsample_bytree,
        "seed":             seed,
        "verbosity":        1,
        # CPU-friendly settings
        "tree_method":      "hist",
        "device":           "cpu",
    }

    log.info("Training XGBoost (n_estimators=%d, max_depth=%d) …", n_estimators, max_depth)
    t0 = time.perf_counter()

    evals_result = {}
    booster = xgb.train(
        params,
        dtrain,
        num_boost_round=n_estimators,
        evals=[(dtrain, "train"), (dtest, "test")],
        evals_result=evals_result,
        verbose_eval=50,
        early_stopping_rounds=30,
    )

    train_secs = time.perf_counter() - t0
    log.info("Training completed in %.1f s", train_secs)

    # ── 5. Evaluate ───────────────────────────────────────────────────────
    raw_probs = booster.predict(dtest)          # shape (N, NUM_CLASSES)
    y_pred    = np.argmax(raw_probs, axis=1)

    acc    = accuracy_score(y_test, y_pred)
    report = classification_report(
        y_test, y_pred,
        target_names=CLASS_NAMES,
        output_dict=True,
    )
    cm = confusion_matrix(y_test, y_pred).tolist()

    precision = report["macro avg"]["precision"]
    recall = report["macro avg"]["recall"]
    f1 = report["macro avg"]["f1-score"]

    log.info("Test accuracy: %.4f (%.2f%%)", acc, acc * 100)
    log.info("\n%s", classification_report(y_test, y_pred, target_names=CLASS_NAMES))

    # ── 6. Save artefacts ─────────────────────────────────────────────────
    model_out = out_path / "posture_classifier.ubj"
    booster.save_model(str(model_out))
    log.info("Model saved → %s", model_out)

    scaler_out = out_path / "feature_scaler.npz"
    np.savez(str(scaler_out), mean=scaler_mean, std=scaler_std, feature_names=FEATURE_NAMES)
    log.info("Scaler saved  → %s", scaler_out)

    # ── 7. Training report & Metadata ─────────────────────────────────────
    import datetime
    
    metadata = {
        "model_version": "v1.0.0",
        "feature_version": "v2.0",
        "training_date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "dataset_version": "v1.0",
        "feature_names": FEATURE_NAMES,
    }
    
    meta_out = out_path / "metadata.json"
    with open(meta_out, "w") as fh:
        json.dump(metadata, fh, indent=2)
    log.info("Metadata saved → %s", meta_out)

    metrics = {
        "accuracy": round(acc, 6),
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "confusion_matrix": cm,
        "n_train": int(len(X_train)),
        "n_test":  int(len(X_test)),
        "n_estimators_used": int(booster.num_boosted_rounds()),
        "training_seconds": round(train_secs, 2),
    }

    metrics_out = out_path / "metrics.json"
    with open(metrics_out, "w") as fh:
        json.dump(metrics, fh, indent=2)
    log.info("Metrics saved → %s", metrics_out)

    return metrics


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="Train the OptiVue posture classifier.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--data", required=True,
        help="Path to posture_data.csv"
    )
    parser.add_argument(
        "--out", default="app/ml/models/artefacts",
        help="Output directory for model artefacts"
    )
    parser.add_argument("--test-size",       type=float, default=0.20)
    parser.add_argument("--n-estimators",    type=int,   default=300)
    parser.add_argument("--max-depth",       type=int,   default=6)
    parser.add_argument("--learning-rate",   type=float, default=0.1)
    parser.add_argument("--subsample",       type=float, default=0.8)
    parser.add_argument("--colsample-bytree",type=float, default=0.8)
    parser.add_argument("--seed",            type=int,   default=42)
    args = parser.parse_args()

    metrics = train_and_save(
        csv_path         = args.data,
        out_dir          = args.out,
        test_size        = args.test_size,
        n_estimators     = args.n_estimators,
        max_depth        = args.max_depth,
        learning_rate    = args.learning_rate,
        subsample        = args.subsample,
        colsample_bytree = args.colsample_bytree,
        seed             = args.seed,
    )
    print(
        f"\n✓ Training complete — accuracy {metrics['test_accuracy_pct']:.2f}%\n"
        f"  Model  : {metrics['model_path']}\n"
        f"  Scaler : {metrics['scaler_path']}\n"
        f"  Report : {Path(metrics['model_path']).parent / 'training_report.json'}"
    )


if __name__ == "__main__":
    _cli()
