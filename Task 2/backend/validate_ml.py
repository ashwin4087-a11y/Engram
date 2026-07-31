"""
validate_ml.py — Quick validation of the ML pipeline modules
=============================================================
Run from the backend directory:  python validate_ml.py
"""
import sys
import os

# Ensure the backend directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

errors = []
successes = []


def check(label, fn):
    try:
        fn()
        successes.append(label)
        print(f"  [OK]   {label}")
    except Exception as e:
        errors.append((label, str(e)))
        print(f"  [FAIL] {label}: {e}")


print("=" * 60)
print("OptiVue ML Pipeline Validation")
print("=" * 60)

# 1. Posture labels
check("posture_labels", lambda: (
    __import__("app.ml.models.posture_labels", fromlist=["PostureClass", "POSTURE_LABELS", "NUM_CLASSES"]),
))

# 2. Feature extractor
check("feature_extractor", lambda: (
    __import__("app.ml.preprocessing.feature_extractor", fromlist=["PostureFeatureExtractor", "FEATURE_NAMES", "NUM_FEATURES"]),
))

# 3. Inference predictor
check("predict (inference)", lambda: (
    __import__("app.ml.inference.predict", fromlist=["predict_posture", "PosturePrediction"]),
))

# 4. Dataset loader
check("dataset_loader", lambda: (
    __import__("app.ml.datasets.dataset_loader", fromlist=["load_dataset"]),
))

# 5. Synthetic data generator
check("generate_synthetic_data", lambda: (
    __import__("app.ml.datasets.generate_synthetic_data", fromlist=["generate_dataset"]),
))

# 6. Training pipeline
check("train", lambda: (
    __import__("app.ml.training.train", fromlist=["train_and_save"]),
))

# 7. Utils
check("model_info", lambda: (
    __import__("app.ml.utils.model_info", fromlist=["artefact_exists"]),
))

# 8. Feature extraction functional test (with dummy data)
def test_feature_extraction():
    import numpy as np
    from app.ml.preprocessing.feature_extractor import feature_extractor, NUM_FEATURES
    
    # Create a mock landmarks object
    class MockLandmark:
        def __init__(self, x, y, z):
            self.x = x
            self.y = y
            self.z = z
    
    class MockFaceLandmarks:
        def __init__(self):
            # 478 landmarks, random but plausible
            rng = np.random.default_rng(42)
            self.landmark = [
                MockLandmark(
                    x=float(rng.uniform(0.2, 0.8)),
                    y=float(rng.uniform(0.2, 0.8)),
                    z=float(rng.uniform(-0.1, 0.1))
                )
                for _ in range(478)
            ]
    
    mock_lm = MockFaceLandmarks()
    vec = feature_extractor.extract(mock_lm, frame_shape=(480, 640))
    assert vec.shape == (NUM_FEATURES,), f"Expected ({NUM_FEATURES},), got {vec.shape}"
    assert vec.dtype == np.float32, f"Expected float32, got {vec.dtype}"
    assert not np.isnan(vec).any(), "Feature vector contains NaN"

check("feature_extraction (functional)", test_feature_extraction)


# 9. Heuristic prediction test
def test_heuristic_prediction():
    import numpy as np
    from app.ml.inference.predict import predict_posture, PosturePrediction
    from app.ml.preprocessing.feature_extractor import NUM_FEATURES
    
    vec = np.zeros(NUM_FEATURES, dtype=np.float32)
    result = predict_posture(vec)
    assert isinstance(result, PosturePrediction), f"Expected PosturePrediction, got {type(result)}"
    assert result.posture in [
        "GOOD_POSTURE", "LEANING_FORWARD", "LEANING_BACKWARD",
        "LOOKING_DOWN", "LOOKING_UP", "HEAD_TILT_LEFT", "HEAD_TILT_RIGHT"
    ], f"Unexpected posture: {result.posture}"
    assert 0.0 <= result.confidence <= 1.0
    assert result.source in ("model", "heuristic"), f"Unexpected source: {result.source}"

check("heuristic_prediction (functional)", test_heuristic_prediction)


# 10. Synthetic data generation test
def test_synthetic_generation():
    from app.ml.datasets.generate_synthetic_data import generate_dataset
    from app.ml.preprocessing.feature_extractor import FEATURE_NAMES
    
    df = generate_dataset(n_samples=70, seed=99)
    assert len(df) == 70, f"Expected 70 rows, got {len(df)}"
    for col in FEATURE_NAMES:
        assert col in df.columns, f"Missing column: {col}"
    assert "label" in df.columns
    assert df["label"].nunique() == 7, f"Expected 7 classes, got {df['label'].nunique()}"

check("synthetic_generation (functional)", test_synthetic_generation)


print()
print("=" * 60)
print(f"Results: {len(successes)} passed, {len(errors)} failed")
print("=" * 60)
if errors:
    print("\nFailed checks:")
    for label, msg in errors:
        print(f"  - {label}: {msg}")
    sys.exit(1)
else:
    print("\nAll checks passed!")
    sys.exit(0)
