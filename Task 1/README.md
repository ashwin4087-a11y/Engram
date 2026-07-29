# VisionBall — Enterprise Monocular Ball Detection System

**VisionBall** is a real-time sports ball detection system optimized for monocular 2D vision. Built to maximize **F1 Score** (accuracy) and **FPS** (throughput), it features a high-performance **FastAPI** backend and a modern, enterprise-grade web dashboard.

---

## 🌟 Key Features

- **Advanced Computer Vision:** Powered by a fine-tuned Ultralytics YOLOv11 Nano model.
- **High-Throughput Runtime:** Exported to **ONNX Runtime** to significantly reduce inference latency.
- **Enterprise Web Dashboard:** A sleek, professional, zero-build web interface for image detection and live camera streaming.
- **Real-Time Telemetry:** Live tracking of FPS, inference latency (milliseconds), and model confidence.
- **Accuracy Optimization:** Built-in benchmarking tools for confidence threshold sweeps to lock in peak F1 scores.

---

## 🚀 Setup & Installation

Follow these steps to set up the project on your local machine.

### 1. Prerequisites
Ensure you have **Python 3.9+** installed on your system.

### 2. Clone the Repository
```bash
git clone https://github.com/yourusername/VisionBall.git
cd VisionBall
```

### 3. Create a Virtual Environment (Recommended)
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

*(Note: The project requires `ultralytics`, `fastapi`, `uvicorn`, `opencv-python`, and `onnxruntime`)*

---

## 🖥️ Usage: Enterprise Dashboard

The primary way to interact with VisionBall is through the Enterprise Web Dashboard.

### Start the Server
Run the FastAPI application using Uvicorn from the root directory:

```bash
python -m uvicorn app.api:app --reload
```

### Access the UI
Open your web browser and navigate to:
**[http://127.0.0.1:8000](http://127.0.0.1:8000)**

From the dashboard, you can:
- **Image Detection:** Upload images for instant ball detection and telemetry analysis.
- **Live Camera:** Connect to your local webcam for real-time inference streaming.

---

## ⚙️ Advanced Usage: Training & Benchmarking

If you wish to retrain the model, run benchmarks, or evaluate the F1 score, use the provided scripts in the `src/` directory.

### Train the Model
Fine-tune the YOLO model on your dataset:
```bash
python src/train.py --data configs/ball.yaml --model yolov8n.pt --epochs 15 --imgsz 640
```

### Export to ONNX
Export PyTorch weights to ONNX format for accelerated inference:
```bash
python src/export_model.py --weights models/best.pt --format onnx --imgsz 640
```

### Evaluate F1 Score
Perform a confidence threshold sweep (0.05–0.95) to find the optimal F1 score:
```bash
python src/eval_f1.py --model models/best.pt --data_split dataset/valid
```

### Benchmark Latency & FPS
Measure inference latency across PyTorch and ONNX backends:
```bash
python src/benchmark_fps.py --pt_model models/best.pt --onnx_model models/best.onnx
```

---

## 📂 Project Structure

```
VisionBall/
├── app/
│   └── api.py                  # FastAPI Backend & Web Server
├── frontend/                   # Enterprise Dashboard UI (HTML/CSS/JS)
├── src/
│   ├── infer.py                # Core YOLO Inference Logic
│   ├── train.py                # Model Training Script
│   ├── export_model.py         # ONNX Export Script
│   ├── eval_f1.py              # F1 Score Evaluation
│   └── benchmark_fps.py        # FPS Benchmarking
├── models/
│   ├── best.pt                 # PyTorch Weights
│   └── best.onnx               # ONNX Runtime Weights
├── results/
│   └── metrics.json            # Auto-generated benchmark telemetry
├── configs/
│   └── ball.yaml               # Dataset configuration
├── requirements.txt            # Python dependencies
└── README.md
```

---

## ⚠️ Cloud Deployment Note
VisionBall's **Live Camera** feature connects directly to your local hardware webcam via OpenCV (`cv2.VideoCapture(0)`). For this reason, the application is designed to be run **locally**. 

If you deploy this application to a cloud serverless environment (like Vercel), the Live Camera feature will not function because the cloud server does not have access to your local webcam. Image detection, however, will continue to work perfectly on cloud platforms that support Docker (e.g., Render, Railway, Google Cloud Run).
