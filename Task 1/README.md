# VisionBall — Monocular Ball Detection (Max F1 Score + Max FPS)

**VisionBall** — Real-time ball detection system optimized for monocular 2D vision under varied lighting, motion blur, and partial occlusion conditions. Built to maximize both **F1 Score** (accuracy) and **FPS** (throughput).

---

## 1. Executive Summary & Strategy

- **Detector Model:** Ultralytics YOLO (YOLOv8n / YOLO11n Nano architecture) single-class fine-tuned for `ball`.
- **High-Throughput Runtime:** Exported to **ONNX Runtime** with optimized execution providers for 2–5x inference latency reduction.
- **Accuracy Optimization:** Domain-specific augmentations (motion blur, lighting jitter, scale cutout) combined with a post-training **Confidence Threshold Sweep (0.05–0.95)** to lock in peak F1 score.
- **Baseline Comparison:** Classical CV pipeline (HSV color mask + Hough Circle transform) for comparative engineering evaluation.

---

## 2. Project Directory Structure

```
Task 1/
├── README.md
├── requirements.txt
├── Task1_BallDetection_Blueprint.md
├── dataset/
│   ├── train/
│   │   ├── images/
│   │   └── labels/
│   ├── valid/
│   │   ├── images/
│   │   └── labels/
│   ├── test/
│   │   ├── images/
│   │   └── labels/
│   ├── data.yaml
│   ├── README.dataset.txt
│   └── README.roboflow.txt
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
│   ├── fps_report.csv
│   └── f1_vs_threshold.png
└── configs/
    └── ball.yaml
```

---

## 3. Quickstart & Installation

```bash
# Navigate to Task 1 directory
cd "Task 1"

# Install dependencies
pip install -r requirements.txt
```

---

## 4. Usage Workflow

### Step 1: Dataset Verification & Synthetic Test Generator
```bash
python src/dataset_prep.py --config configs/ball.yaml
```

### Step 2: Train Model
Fine-tune YOLO Nano on the ball dataset:
```bash
python src/train.py --data configs/ball.yaml --model yolov8n.pt --epochs 15 --imgsz 640
```

### Step 3: Export Model to ONNX
Export fine-tuned PyTorch weights to ONNX format for accelerated inference:
```bash
python src/export_model.py --weights models/best.pt --format onnx --imgsz 640
```

### Step 4: Evaluate F1 Score & Threshold Sweep
Perform confidence threshold sweep across 0.05–0.95 on validation set:
```bash
python src/eval_f1.py --model models/best.pt --data_split dataset/valid
```

### Step 5: Benchmark Latency & FPS
Measure inference latency and average FPS across backends:
```bash
python src/benchmark_fps.py --pt_model models/best.pt --onnx_model models/best.onnx
```

### Step 6: Run Live Stream / Webcam Demo
```bash
# Webcam live detection feed
python app/live_demo.py --source 0 --model models/best.pt

# Video file demo
python app/live_demo.py --source path/to/video.mp4 --model models/best.onnx
```

### Step 7: Launch Streamlit Dashboard
```bash
streamlit run app/streamlit_app.py
```

---

## 5. Metrics & Combined Score Formula

The overall performance score balances accuracy and speed:

$$\text{Combined Score} = (F1 \times 0.6) + (\text{Normalized FPS} \times 0.4)$$

All benchmark numbers, optimal thresholds, and F1 curves are logged in `results/metrics.json` and rendered in the Streamlit UI.
