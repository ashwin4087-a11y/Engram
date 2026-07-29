import os
import sys
import time
import cv2
import numpy as np
import argparse

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.infer import BallDetector
from src.utils import draw_detections

def run_live_demo(
    source: str = "0",
    model_path: str = "models/best.pt",
    conf_thres: float = 0.25,
    output_path: str = None
):
    """
    Live video stream or webcam ball detection demo with real-time FPS overlay.
    """
    print(f"\n==========================================")
    print(f"Starting VisionBall Live Demo")
    print(f"Video Source: {source}")
    print(f"Model Path: {model_path} | Conf Thres: {conf_thres}")
    print(f"Press 'q' or ESC in display window to exit.")
    print(f"==========================================\n")

    # Initialize Detector
    detector = None
    if os.path.exists(model_path):
        try:
            detector = BallDetector(model_path=model_path, conf_thres=conf_thres)
        except Exception as e:
            print(f"Error loading detector model: {e}")

    # Determine input source
    is_webcam = source.isdigit()
    cap_source = int(source) if is_webcam else source
    cap = cv2.VideoCapture(cap_source)

    if not cap.isOpened():
        print(f"Warning: Could not open video source '{source}'. Launching synthetic live animation stream...")
        run_synthetic_animation_demo(detector)
        return

    writer = None
    if output_path:
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps_in = cap.get(cv2.CAP_PROP_FPS) or 30.0
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps_in, (w, h))

    prev_time = time.perf_counter()
    fps_smooth = 0.0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("End of video stream reached.")
            break

        curr_time = time.perf_counter()
        loop_time = curr_time - prev_time
        prev_time = curr_time
        fps_instant = 1.0 / loop_time if loop_time > 0 else 0.0
        fps_smooth = 0.9 * fps_smooth + 0.1 * fps_instant if fps_smooth > 0 else fps_instant

        boxes, scores, class_ids = [], [], []
        if detector is not None:
            boxes, scores, class_ids = detector.predict(frame)

        annotated_frame = draw_detections(
            frame,
            boxes,
            scores,
            class_ids=class_ids,
            fps=fps_smooth
        )

        if writer is not None:
            writer.write(annotated_frame)

        try:
            cv2.imshow("VisionBall — Live Demo", annotated_frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord('q')):
                print("Exit requested by user.")
                break
        except Exception:
            # Headless environment
            pass

    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()

def run_synthetic_animation_demo(detector=None):
    """
    Fallback animated bouncing ball demo for headless/testing environments.
    """
    w, h = 640, 480
    cx, cy = 100, 100
    vx, vy = 8, 6
    radius = 30

    prev_time = time.perf_counter()
    fps_smooth = 0.0

    print("Running Bouncing Ball Demo Mode. Press 'q' to stop.")
    for frame_idx in range(300):
        curr_time = time.perf_counter()
        loop_time = curr_time - prev_time
        prev_time = curr_time
        fps_instant = 1.0 / loop_time if loop_time > 0 else 0.0
        fps_smooth = 0.9 * fps_smooth + 0.1 * fps_instant if fps_smooth > 0 else fps_instant

        # Bouncing logic
        cx += vx
        cy += vy
        if cx - radius <= 0 or cx + radius >= w:
            vx = -vx
        if cy - radius <= 0 or cy + radius >= h:
            vy = -vy

        frame = np.full((h, w, 3), (40, 40, 40), dtype=np.uint8)
        cv2.circle(frame, (cx, cy), radius, (0, 165, 255), -1)
        cv2.circle(frame, (cx - radius // 3, cy - radius // 3), 6, (255, 255, 255), -1)

        boxes, scores, class_ids = [], [], []
        if detector is not None:
            boxes, scores, class_ids = detector.predict(frame)
        else:
            boxes = [[float(cx - radius), float(cy - radius), float(cx + radius), float(cy + radius)]]
            scores = [0.98]
            class_ids = [0]

        annotated_frame = draw_detections(frame, boxes, scores, class_ids=class_ids, fps=fps_smooth)

        try:
            cv2.imshow("VisionBall — Live Demo", annotated_frame)
            if cv2.waitKey(30) & 0xFF in (27, ord('q')):
                break
        except Exception:
            pass

    cv2.destroyAllWindows()

def main():
    parser = argparse.ArgumentParser(description="VisionBall — Live Video Stream Demo")
    parser.add_argument("--source", type=str, default="0", help="Webcam index (0) or path to input video file")
    parser.add_argument("--model", type=str, default="models/best.pt", help="Path to detector model weights (.pt or .onnx)")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--output", type=str, default=None, help="Optional output video file path")
    args = parser.parse_args()

    run_live_demo(
        source=args.source,
        model_path=args.model,
        conf_thres=args.conf,
        output_path=args.output
    )

if __name__ == "__main__":
    main()
