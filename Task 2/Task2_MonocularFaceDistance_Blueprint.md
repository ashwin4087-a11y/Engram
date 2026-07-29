# Task 2 — Monocular Face Distance Estimation
### Complete Project Blueprint — HackTronix 2.0, Track B (AI Qualifier)

---

## 1. Problem Restated

From a single 2D camera image, estimate:
- **Depth (Z)**: distance from camera to face, in meters.
- **Angle (θ)**: horizontal deviation of the face from the camera's optical axis.

Given, with pinhole camera model assumed:

```
Z = (f × W) / w_px
θ = arctan((x − c_x) / f)
```

Where `f` = focal length (px), `W` = real average face width (~0.14–0.16 m), `w_px` = detected face width in pixels, `(x, c_x)` = face center x and image center x. Acceptable error: ±50–150 cm.

The two things you actually need to engineer well are: **(a) a reliable face width/center detector**, and **(b) an accurate focal length `f`**, since the formula itself is one line of math.

---

## 2. Core Strategy

| Component | Choice | Why |
|---|---|---|
| Face detector | **MediaPipe Face Detection** (or Face Mesh for higher precision landmarks) | Fast (CPU real-time), gives stable bounding box + landmark points for width measurement, no GPU needed |
| Face width measurement | Use **inter-landmark distance** (e.g. left cheek to right cheek, or bbox width) rather than raw bbox width | Bounding boxes jitter with pose; landmark-based width is more stable frame-to-frame |
| Focal length `f` | **Camera calibration via known-distance reference**, not guessed from EXIF/spec sheet | This is the #1 source of error in this task — get it right and the whole system meets the ±50–150cm bar easily |
| Smoothing | **Exponential moving average or simple Kalman filter** on `(w_px, x)` across frames | Raw per-frame detection is noisy; smoothing meaningfully improves stability without adding real latency |
| Output | `(Z, θ)` printed/overlaid live + logged to CSV for accuracy validation | Matches "Expected Output" in the problem statement, and gives you your own accuracy report for the demo |

---

## 3. Tech Stack

- **Language:** Python 3.10+
- **Face detection/landmarks:** MediaPipe (`mediapipe.solutions.face_detection` or `face_mesh`)
- **CV/utility:** OpenCV, NumPy
- **Calibration:** OpenCV (`cv2.VideoCapture`), simple script + tape measure / ruler
- **Smoothing:** SciPy or a small custom Kalman filter / EMA
- **Visualization/demo:** OpenCV live overlay, optional Streamlit/Matplotlib for the accuracy report

---

## 4. Folder / File Structure

```
Task 2/
├── README.md
├── requirements.txt
├── calibration/
│   ├── calibrate_focal_length.py
│   ├── calibration_images/
│   └── focal_length.json
├── src/
│   ├── __init__.py
│   ├── face_detector.py
│   ├── distance_estimator.py
│   ├── smoothing.py
│   ├── main.py
│   └── utils.py
├── tests/
│   ├── ground_truth_log.csv
│   ├── accuracy_eval.py
│   └── generate_error_report.py
├── results/
│   ├── accuracy_report.png
│   └── error_metrics.json
└── docs/
    └── design_notes.md
```

---

## 5. File-by-File Blueprint

### `README.md`
Setup steps, how to run calibration then the live estimator, explanation of the math model, and final accuracy numbers vs the ±50–150cm target.

### `requirements.txt`
```
mediapipe
opencv-python
numpy
scipy
matplotlib
pandas
```

### `calibration/calibrate_focal_length.py`
- Have the user stand at a **known distance `Z_known`** (e.g. exactly 1.0 m, measured with tape) from the camera, facing it.
- Detect face width in pixels (`w_px_known`) at that distance.
- Rearranged pinhole formula: **`f = (w_px_known × Z_known) / W`**.
- Repeat at 2–3 known distances (e.g. 0.5m, 1m, 1.5m) and average `f` for robustness against detector noise.
- Save result to `focal_length.json` (`{"f": <value>, "W": 0.15, "samples": [...]}`).

### `calibration/focal_length.json`
Persisted calibration output consumed by `distance_estimator.py` at runtime — avoids re-calibrating every session.

### `src/face_detector.py`
- Wraps MediaPipe: given a BGR frame, returns `(x, y, w_px)` — face center pixel coords and face width in pixels — plus a detection confidence.
- Uses **landmark-based width** (e.g. distance between left/right face-boundary landmarks in Face Mesh) as the primary measurement, with bbox width as fallback if landmarks aren't available.

### `src/distance_estimator.py`
- Implements the exact math model:
  ```python
  def estimate(x, w_px, f, W, image_center_x):
      Z = (f * W) / w_px
      theta = math.atan2(x - image_center_x, f)
      return Z, math.degrees(theta)
  ```
- Loads `f` and `W` from `calibration/focal_length.json`.
- Also exposes a per-frame **confidence/uncertainty flag** (e.g. flag low confidence when `w_px` is very small/large, indicating detector unreliability at extreme distances).

### `src/smoothing.py`
- EMA smoother: `smoothed = alpha * new + (1 - alpha) * smoothed_prev`, applied to `w_px` and `x` before feeding `distance_estimator.py` — reduces jitter in the displayed `(Z, θ)`.
- (Optional, more judge-impressive) simple constant-velocity Kalman filter over `(w_px, x)`.

### `src/main.py`
- Live webcam loop: capture frame → `face_detector.py` → `smoothing.py` → `distance_estimator.py` → overlay `Z` (in meters) and `θ` (in degrees) on the video feed in real time, plus an FPS counter.
- Logs each frame's `(timestamp, Z, theta, w_px, x)` to `tests/ground_truth_log.csv` when in "logging mode" for accuracy testing.

### `src/utils.py`
- Shared helpers: drawing text/overlay boxes, JSON load/save, image center calc.

### `tests/ground_truth_log.csv`
- Captured during controlled tests: place face at known distances (e.g. 0.5m, 1m, 1.5m, 2m, 3m) and known horizontal offsets, log predicted `Z, θ` alongside the manually measured ground truth.

### `tests/accuracy_eval.py`
- Loads the ground-truth log, computes **Mean Absolute Error (MAE)** and **max error** for `Z` (should stay within 0.5–1.5 m per the spec) and for `θ`.
- Flags any distance range where error exceeds the ±50–150cm bound, so you know the system's honest operating range.

### `tests/generate_error_report.py`
- Produces `results/accuracy_report.png` — a plot of predicted vs. actual distance across the tested range (a straight y=x line means perfect accuracy; this plot is a strong demo visual for judges).

### `docs/design_notes.md`
- Explains why landmark-based width beats bbox width, the calibration procedure and why multi-distance averaging was used, and the smoothing method chosen — this is what answers "how did you validate accuracy?" convincingly.

---

## 6. Build Order (Execution Roadmap)

1. **Hour 0–1:** Set up repo, install MediaPipe/OpenCV, get raw face bbox detection running live.
2. **Hour 1–2:** Switch to Face Mesh landmark-based width measurement (more stable than raw bbox).
3. **Hour 2–3:** Build `calibrate_focal_length.py`, run calibration at 2–3 known distances, save `focal_length.json`.
4. **Hour 3–4:** Implement `distance_estimator.py` with the exact `Z`/`θ` formulas; verify against calibration points (should read back ~ground truth at the calibration distances themselves).
5. **Hour 4–5:** Add EMA/Kalman smoothing; wire into `main.py` live overlay with FPS counter.
6. **Hour 5–6:** Run controlled accuracy tests across 5+ distances and a few horizontal offsets; log to CSV.
7. **Hour 6–7:** Build `accuracy_eval.py` + `generate_error_report.py`, produce the predicted-vs-actual plot.
8. Buffer time: README, design notes, rehearse live demo (walk toward/away from camera on stage).

---

## 7. Judge Talking Points to Prepare

- Why calibration matters more than the formula itself, and how you calibrated `f` (multi-distance averaging).
- Why you used landmark-based width instead of raw bounding-box width (stability).
- Your own measured error numbers vs. the ±50–150cm spec, with the accuracy plot as evidence.
- What breaks the system (very close/far distances, extreme head angles) and how you detect/flag that with the confidence check.
