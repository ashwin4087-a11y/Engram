# Task 1 — Ball Detection (Max F1 Score + Max FPS)
### Complete Project Blueprint — HackTronix 2.0, Track B (AI Qualifier)

---

## 1. Problem Restated

Build a real-time, monocular (single 2D camera) ball detection system that:
- Detects and localizes a ball under varied conditions (lighting, background, motion blur, partial occlusion).
- Maximizes **F1 Score** (primary metric).
- Maximizes **FPS** on the target hardware (secondary metric).
- Is judged on a **Combined Score** that rewards both.

The winning strategy is not "biggest model" — it's the best **accuracy-per-millisecond** tradeoff, with a defensible engineering story for why you picked that tradeoff.

---

## 2. Core Strategy

Use a small, purpose-built object detector rather than a general heavy one:

| Choice | Why |
|---|---|
| **YOLOv8n / YOLO11n (nano)** via Ultralytics | Best speed/accuracy ratio in its class, easy to fine-tune, exports cleanly to ONNX/TensorRT |
| Single-class detection (`ball`) | Removes multi-class overhead, lets you shrink the head and raise confidence separation |
| Fine-tune on a ball-specific dataset (Roboflow "sports ball" / "soccer ball" / "basketball" public datasets, merged + augmented) | General COCO "sports ball" class is weak; domain-specific fine-tuning is what wins F1 |
| Export to **ONNX Runtime** or **TensorRT** (if GPU present) for inference | 2-5x FPS gain over raw PyTorch inference with no accuracy loss |
| Confidence-threshold + NMS-IoU tuning on a validation set | This is a *free* F1 gain most teams skip — sweep thresholds and pick the F1-maximizing point rather than the default 0.25 |

**Fallback / comparison track (for the demo, to show engineering rigor):** also implement a classical CV baseline (Hough Circle Transform + color/contour filtering) to show the F1/FPS tradeoff curve against the deep-learning model — this is a strong judge talking point ("we quantified why we chose YOLO over classical CV").

---

## 3. Tech Stack

- **Language:** Python 3.10+
- **Detection model:** Ultralytics YOLOv8n / YOLO11n
- **Inference runtime:** ONNX Runtime (CPU) or TensorRT (if NVIDIA GPU available)
- **CV/utility:** OpenCV, NumPy
- **Dataset tooling:** Roboflow (annotation + augmentation + export), Albumentations (extra augmentation)
- **Benchmarking:** `time.perf_counter`, `torch.cuda.Event` (if GPU), custom FPS/F1 harness
- **Demo/UI:** Streamlit or a simple OpenCV `imshow` live overlay
- **Experiment tracking (optional, judge-impressive):** Weights & Biases or a simple CSV/JSON logger

---

## 4. Folder / File Structure

```
Task 1/
├── README.md
├── requirements.txt
├── configs/
│   └── ball.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   └── ball_dataset.yaml
├── src/
│   ├── __init__.py
│   ├── dataset_prep.py
│   ├── augment.py
│   ├── train.py
│   ├── export_model.py
│   ├── infer.py
│   ├── classical_cv_baseline.py
│   ├── eval_f1.py
│   ├── benchmark_fps.py
│   └── utils.py
├── app/
│   ├── live_demo.py
│   └── streamlit_app.py
├── models/
│   ├── best.pt
│   └── best.onnx
├── results/
│   ├── metrics.json
│   ├── f1_vs_threshold.png
│   └── fps_report.csv
└── docs/
    └── design_notes.md
```

---

## 5. File-by-File Blueprint

### `README.md`
Project overview, setup instructions, how to run training/inference/benchmark, final F1/FPS numbers, and a one-paragraph summary of the chosen architecture and why.

### `requirements.txt`
```
ultralytics
opencv-python
onnxruntime          # or onnxruntime-gpu
numpy
albumentations
streamlit
pandas
matplotlib
```

### `configs/ball.yaml`
Ultralytics data config: paths to train/val/test image + label folders, `nc: 1`, `names: ['ball']`.

### `data/dataset_prep.py` *(logic lives in `src/dataset_prep.py`)*
- Downloads/merges public ball datasets (Roboflow universe) into YOLO format (`images/`, `labels/`).
- Splits into train/val/test (e.g. 80/10/10).
- Validates label integrity (bounding boxes within image bounds, no empty labels for positive images).

### `src/augment.py`
- Albumentations pipeline: motion blur, brightness/contrast jitter, random occlusion (cutout), background swap, scale jitter (simulates near/far balls) — directly targets "varied conditions" requirement in the problem statement.

### `src/train.py`
- Loads YOLOv8n/YOLO11n pretrained weights, fine-tunes on the ball dataset.
- Key training args to expose: `imgsz` (try 416 vs 640 — smaller = faster, test F1 impact), `epochs`, `batch`, `patience` (early stopping), `lr0`.
- Logs training curves; saves `best.pt`.

### `src/export_model.py`
- Exports `best.pt` → ONNX (and TensorRT `.engine` if CUDA GPU is available) with `half=True` (FP16) for speed.
- Validates exported model output matches PyTorch output (sanity check on a few images).

### `src/infer.py`
- Loads ONNX/TensorRT model.
- Preprocess (letterbox resize, normalize) → inference → postprocess (NMS, threshold filter) → returns bounding boxes + confidence.
- Single-image and video-stream modes.

### `src/classical_cv_baseline.py`
- HSV color-masking + Hough Circle Transform baseline detector, for the comparison/demo talking point.

### `src/eval_f1.py`
- Computes Precision/Recall/F1 against a labeled validation/test set using IoU matching (e.g. IoU ≥ 0.5 = true positive).
- **Confidence-threshold sweep**: runs eval across thresholds 0.05–0.95, plots F1 vs threshold, selects and logs the optimal threshold → `f1_vs_threshold.png`.

### `src/benchmark_fps.py`
- Runs N inference passes (warm-up excluded) on the target hardware, reports mean/median FPS, latency percentiles (p50/p95/p99).
- Benchmarks separately: PyTorch `.pt`, ONNX, and (if available) TensorRT — produces `fps_report.csv` showing the speed ladder.

### `src/utils.py`
- Shared helpers: IoU calculation, letterbox resize, drawing boxes, config loading.

### `app/live_demo.py`
- OpenCV webcam loop: capture → `infer.py` → draw bounding box + confidence + live FPS counter overlay. This is the **judge-facing demo**.

### `app/streamlit_app.py`
- Optional polished web UI: upload image/video or use webcam, shows detection + F1/FPS dashboard reading from `results/metrics.json`. High WOW-factor, low effort using Streamlit's built-in components.

### `results/metrics.json`
- Final reported numbers: F1, Precision, Recall, FPS (per backend), chosen confidence threshold, combined score.

### `docs/design_notes.md`
- Documents the accuracy/speed tradeoff decisions made (model size chosen, imgsz chosen, threshold chosen) — this is what answers judge questions like "why this model?" convincingly.

---

## 6. Evaluation / Combined Score

Define your own transparent combined score (document it in README so judges see the reasoning), e.g.:

```
Combined Score = (F1 × 0.6) + (normalized_FPS × 0.4)
normalized_FPS = min(FPS / target_FPS, 1.0)   # e.g. target_FPS = 30
```

Report this alongside raw F1 and FPS — judges reward teams who quantify their own tradeoff rather than just claiming "fast and accurate."

---

## 7. Build Order (Execution Roadmap)

1. **Hour 0–1:** Set up repo structure, `requirements.txt`, get a public ball dataset merged into YOLO format.
2. **Hour 1–2:** Baseline train YOLOv8n at default settings — get *something* detecting to de-risk the demo early.
3. **Hour 2–4:** Add augmentation pipeline, retrain, evaluate F1 on val set.
4. **Hour 4–5:** Export to ONNX (+TensorRT if GPU), benchmark FPS across backends.
5. **Hour 5–6:** Threshold sweep for optimal F1, lock in final model + threshold.
6. **Hour 6–7:** Build `live_demo.py` with FPS overlay — this is your live demo asset.
7. **Hour 7–8:** Classical CV baseline for the comparison talking point; write `design_notes.md`.
8. Buffer time: Streamlit dashboard, README polish, rehearse demo.

---

## 8. Judge Talking Points to Prepare

- Why YOLOv8n/YOLO11n over a bigger model (speed/accuracy curve, shown with your own benchmark data).
- How you specifically improved F1 beyond default training (augmentation for "varied conditions," threshold tuning).
- The ONNX/TensorRT export gain, with real before/after FPS numbers.
- The classical-CV vs deep-learning comparison as evidence of engineering depth.
