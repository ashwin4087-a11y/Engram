import os
import sys
import json
import cv2
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

# Add src/ directory to system path for imports
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.infer import BallDetector
from src.utils import draw_detections

st.set_page_config(
    page_title="VisionBall | Image Detection",
    page_icon="⚽",
    layout="wide"
)

# Custom CSS for UI/UX matching the frontend design
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap');

html, body, [class*="st-"] {
    font-family: 'Inter', sans-serif;
}

/* Metric card styling */
[data-testid="stMetric"] {
    background-color: #ffffff;
    padding: 1.25rem;
    border-radius: 0.75rem;
    border: 1px solid #DBE2EF;
    box-shadow: 0px 1px 3px 0px rgba(0, 0, 0, 0.05), 0px 1px 2px -1px rgba(0, 0, 0, 0.05);
}

[data-testid="stMetricLabel"] {
    font-size: 12px;
    font-weight: 600;
    color: #585f6a;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

[data-testid="stMetricValue"] {
    font-size: 32px;
    font-weight: 700;
    color: #112D4E;
    margin-top: 0.5rem;
}

/* Primary Button Styling */
.stButton > button {
    background-color: #3F72AF;
    color: white;
    border-radius: 0.5rem;
    font-weight: 500;
    padding: 0.5rem 1.5rem;
    border: none;
    transition: all 0.2s ease-in-out;
}
.stButton > button:hover {
    background-color: #004882;
    color: white;
}

/* Expander/Info card styling */
[data-testid="stInfo"] {
    background-color: rgba(63, 114, 175, 0.05);
    border: 1px solid rgba(63, 114, 175, 0.2);
    border-radius: 0.75rem;
    color: #112D4E;
}
</style>
""", unsafe_allow_html=True)

# Title & Header
st.markdown("<h1 style='color: #112D4E;'>⚽ VisionBall <span style='font-weight: 400; color: #585f6a;'>| Image Detection</span></h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #585f6a; font-size: 18px;'>Enterprise Analytics: High-precision object and motion analysis.</p>", unsafe_allow_html=True)

# Sidebar Controls
st.sidebar.markdown("<h2 style='color: #112D4E;'>⚙️ Model Settings</h2>", unsafe_allow_html=True)
model_choice = st.sidebar.selectbox(
    "Select Backend Model:",
    ["PyTorch (.pt)", "ONNX Runtime (.onnx)", "Classical CV Baseline"],
    index=0
)

weights_map = {
    "PyTorch (.pt)": "models/best.pt",
    "ONNX Runtime (.onnx)": "models/best.onnx",
    "Classical CV Baseline": "classical"
}
selected_path = weights_map[model_choice]

conf_thres = st.sidebar.slider(
    "Confidence Threshold:",
    min_value=0.05,
    max_value=0.95,
    value=0.25,
    step=0.05
)

iou_thres = st.sidebar.slider(
    "NMS IoU Threshold:",
    min_value=0.10,
    max_value=0.80,
    value=0.45,
    step=0.05
)

st.sidebar.markdown("<hr style='border-color: #DBE2EF;'>", unsafe_allow_html=True)
st.sidebar.info("💡 **Analyst Tip**: Adjust the confidence threshold to balance precision and recall depending on the visual noise in your footage.")

# Load Metrics Summary if available
metrics_file = "results/metrics.json"
metrics_data = {}
if os.path.exists(metrics_file):
    try:
        with open(metrics_file, "r") as f:
            metrics_data = json.load(f)
    except Exception:
        pass

# Top KPI metrics section (Styled like the HTML grid)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Peak F1 Score", f"{metrics_data.get('max_f1_score', 'N/A')}")
col2.metric("Optimal Confidence", f"{metrics_data.get('optimal_confidence_threshold', 0.25)}")
col3.metric("Max FPS", f"{metrics_data.get('max_fps', 'N/A')} FPS")
col4.metric("Fastest Engine", f"{metrics_data.get('fastest_backend', 'PyTorch / ONNX')}")

st.divider()

# Mode Selection
input_mode = st.radio("Select Input Source:", ["Upload Image", "Sample Demo Image", "Evaluation & Benchmark Dashboard"], horizontal=True)

if input_mode == "Upload Image":
    uploaded_file = st.file_uploader("Upload an image (JPG, PNG, JPEG):", type=["jpg", "png", "jpeg"])
    if uploaded_file is not None:
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, 1)

        st.markdown("<h3 style='color: #112D4E;'>Detection Result</h3>", unsafe_allow_html=True)
        
        detector = None
        if os.path.exists(selected_path):
            detector = BallDetector(model_path=selected_path, conf_thres=conf_thres, iou_thres=iou_thres)

        if detector:
            boxes, scores, class_ids = detector.predict(image)
            annotated = draw_detections(image, boxes, scores, class_ids)
            
            c_img1, c_img2 = st.columns(2)
            c_img1.image(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), caption="Original Source", use_container_width=True)
            c_img2.image(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB), caption=f"Detection Overlay ({len(boxes)} object(s) found)", use_container_width=True)

            if len(boxes) > 0:
                st.markdown("### 📊 Detection Breakdown")
                df_det = pd.DataFrame({
                    "ID": [f"#VB-{i+1:03d}" for i in range(len(boxes))],
                    "Confidence": [f"{s:.4f}" for s in scores],
                    "Bounding Box [x1, y1, x2, y2]": [f"{[round(c, 1) for c in b]}" for b in boxes]
                })
                st.dataframe(df_det, use_container_width=True)
            else:
                st.info("No balls detected above the confidence threshold.")
        else:
            st.warning(f"Model file `{selected_path}` not found. Train the model first via `python src/train.py`.")

elif input_mode == "Sample Demo Image":
    # Generate synthetic image for immediate testing
    w, h = 640, 480
    demo_img = np.full((h, w, 3), (249, 247, 247), dtype=np.uint8) # Match background #F9F7F7 roughly
    cv2.circle(demo_img, (320, 240), 45, (175, 114, 63), -1) # BGR for #3F72AF
    cv2.circle(demo_img, (305, 225), 10, (255, 255, 255), -1)

    c_img1, c_img2 = st.columns(2)
    c_img1.image(cv2.cvtColor(demo_img, cv2.COLOR_BGR2RGB), caption="Sample Synthetic Input", use_container_width=True)

    if os.path.exists(selected_path):
        detector = BallDetector(model_path=selected_path, conf_thres=conf_thres, iou_thres=iou_thres)
        boxes, scores, class_ids = detector.predict(demo_img)
        annotated = draw_detections(demo_img, boxes, scores, class_ids)
        c_img2.image(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB), caption="Detection Output", use_container_width=True)
    else:
        c_img2.image(cv2.cvtColor(demo_img, cv2.COLOR_BGR2RGB), caption="Sample Image (Model file pending training)", use_container_width=True)

elif input_mode == "Evaluation & Benchmark Dashboard":
    st.markdown("<h2 style='color: #112D4E;'>📈 Performance & Accuracy Reports</h2>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("<h3 style='color: #112D4E; font-size: 1.25rem;'>F1 Score vs Confidence Sweep</h3>", unsafe_allow_html=True)
        plot_path = "results/f1_vs_threshold.png"
        if os.path.exists(plot_path):
            st.image(plot_path, use_container_width=True)
        else:
            st.info("Run `python src/eval_f1.py` to generate the F1 vs Confidence curve.")

    with col_right:
        st.markdown("<h3 style='color: #112D4E; font-size: 1.25rem;'>Inference Latency & FPS Report</h3>", unsafe_allow_html=True)
        csv_path = "results/fps_report.csv"
        if os.path.exists(csv_path):
            df_fps = pd.read_csv(csv_path)
            st.dataframe(df_fps, use_container_width=True)
        else:
            st.info("Run `python src/benchmark_fps.py` to generate the FPS comparison report.")
