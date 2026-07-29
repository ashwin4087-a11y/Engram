# VisionBall — Engineering Design Notes

## 1. Model Architecture Rationale

- **Why YOLO Nano (YOLOv8n / YOLO11n)?**
  Monocular real-time tracking requires high frame rates (>60 FPS on GPU / >30 FPS on CPU). Heavy architectures like ResNet-101 based Faster R-CNN or YOLOv8x sacrifice up to 80% inference speed for marginal accuracy gains. YOLO Nano provides an ideal latency footprint (~3ms GPU / ~20ms CPU) while achieving >0.90 F1 on single-class ball detection when fine-tuned on target datasets.

- **Single-Class Head Reduction**
  By configuring `nc: 1` (`ball`), the prediction head channels shrink significantly, eliminating multi-class classification branch overhead.

## 2. Speed Optimization & Acceleration

- **ONNX Runtime Export:**
  Converting PyTorch graphs (`.pt`) to static/dynamic ONNX graphs eliminates Python runtime overhead, enables graph optimization pass (node fusion, constant folding), and delivers 2–4x FPS gains on standard CPUs.

- **Resolution Selection (416 vs 640):**
  - **640x640:** Higher F1 score on small/distant balls; standard baseline.
  - **416x416:** 2.2x faster inference latency for fast motion streaming applications.

## 3. Accuracy Optimization (F1 Maximization)

- **Threshold Sweep Strategy:**
  Standard object detection implementations default to a arbitrary confidence threshold of `0.25`. By sweeping thresholds from 0.05 to 0.95 against a ground-truth validation set (`src/eval_f1.py`), we identify the precise point where Precision and Recall intersect to yield the peak F1 score.

- **Augmentations for Environmental Variance:**
  Motion blur, brightness/contrast jitter, and random cutout are applied during training to handle real-world challenges (shadows, motion blur during fast passes, partial occlusions behind players/objects).

## 4. Engineering Comparison Baseline

- **Classical CV vs Deep Learning:**
  A classical Hough Circle Transform + HSV color filtering baseline (`src/classical_cv_baseline.py`) was implemented. While classical CV achieves >150 FPS, its F1 score drops sharply under dynamic lighting, background clutter, or non-spherical motion blurs—quantifying why fine-tuned YOLO is the winning engineering choice.
