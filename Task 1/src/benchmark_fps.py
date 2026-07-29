import os
import sys
import time
import json
import csv
import cv2
import numpy as np
import argparse
from typing import Dict, List, Any

# Ensure src/ is on sys.path for sibling imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from infer import BallDetector
from classical_cv_baseline import ClassicalBallDetector
from utils import ensure_dirs

def benchmark_detector(
    model_path: str = None,
    use_classical: bool = False,
    num_warmup: int = 10,
    num_runs: int = 100,
    imgsz: int = 640
) -> Dict[str, Any]:
    """
    Runs latency and FPS benchmark over specified number of iterations.
    """
    # Create a realistic test frame (solid background with a circle, not random noise
    # which causes HoughCircles to detect thousands of false circles and hang)
    dummy_frame = np.full((imgsz, imgsz, 3), (120, 140, 100), dtype=np.uint8)
    cv2.circle(dummy_frame, (imgsz // 2, imgsz // 2), 40, (0, 165, 255), -1)

    if use_classical:
        backend_name = "Classical CV (Hough + Color)"
        detector = ClassicalBallDetector()
    elif model_path and os.path.exists(model_path):
        detector = BallDetector(model_path=model_path, imgsz=imgsz)
        backend_name = f"YOLO ({detector.backend.upper()})"
    else:
        raise ValueError("Invalid model path or detector choice.")

    print(f"\nBenchmarking: {backend_name}...")

    # Warmup runs
    for _ in range(num_warmup):
        detector.predict(dummy_frame)

    # Benchmark runs
    latencies = []
    for _ in range(num_runs):
        t0 = time.perf_counter()
        detector.predict(dummy_frame)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)  # Convert to ms

    mean_latency = float(np.mean(latencies))
    median_latency = float(np.median(latencies))
    p95_latency = float(np.percentile(latencies, 95))
    p99_latency = float(np.percentile(latencies, 99))
    fps = float(1000.0 / mean_latency) if mean_latency > 0 else 0.0

    print(f"  Mean Latency  : {mean_latency:.2f} ms")
    print(f"  Median (p50)  : {median_latency:.2f} ms")
    print(f"  95th Pct (p95): {p95_latency:.2f} ms")
    print(f"  99th Pct (p99): {p99_latency:.2f} ms")
    print(f"  Average FPS   : {fps:.2f} FPS")

    return {
        "backend": backend_name,
        "mean_latency_ms": round(mean_latency, 2),
        "p50_latency_ms": round(median_latency, 2),
        "p95_latency_ms": round(p95_latency, 2),
        "p99_latency_ms": round(p99_latency, 2),
        "fps": round(fps, 2),
        "num_runs": num_runs
    }

def run_all_benchmarks(
    pt_model: str = "models/best.pt",
    onnx_model: str = "models/best.onnx",
    results_dir: str = "results",
    num_runs: int = 100
):
    """
    Executes benchmark comparison across PyTorch, ONNX, and Classical CV backends.
    """
    ensure_dirs(results_dir)
    results = []

    if os.path.exists(pt_model):
        res_pt = benchmark_detector(model_path=pt_model, num_runs=num_runs)
        results.append(res_pt)

    if os.path.exists(onnx_model):
        res_onnx = benchmark_detector(model_path=onnx_model, num_runs=num_runs)
        results.append(res_onnx)

    # Benchmark Classical CV baseline
    res_classical = benchmark_detector(use_classical=True, num_runs=num_runs)
    results.append(res_classical)

    # Save to fps_report.csv
    csv_path = os.path.join(results_dir, "fps_report.csv")
    fieldnames = ["backend", "fps", "mean_latency_ms", "p50_latency_ms", "p95_latency_ms", "p99_latency_ms", "num_runs"]
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    print(f"\nFPS Report saved to: {csv_path}")

    # Update metrics.json
    metrics_path = os.path.join(results_dir, "metrics.json")
    metrics_data = {}
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, 'r') as f:
                metrics_data = json.load(f)
        except Exception:
            pass

    metrics_data["benchmark_results"] = results
    if results:
        # Find best FPS
        best_backend = max(results, key=lambda x: x["fps"])
        metrics_data["max_fps"] = best_backend["fps"]
        metrics_data["fastest_backend"] = best_backend["backend"]

    with open(metrics_path, 'w') as f:
        json.dump(metrics_data, f, indent=4)
    print(f"Updated metrics summary in: {metrics_path}")

def main():
    parser = argparse.ArgumentParser(description="Benchmark Ball Detection FPS & Latency Ladder")
    parser.add_argument("--pt_model", type=str, default="models/best.pt", help="Path to PyTorch model weights")
    parser.add_argument("--onnx_model", type=str, default="models/best.onnx", help="Path to ONNX model weights")
    parser.add_argument("--results", type=str, default="results", help="Directory to save benchmark reports")
    parser.add_argument("--runs", type=int, default=100, help="Number of benchmark iterations")
    args = parser.parse_args()

    run_all_benchmarks(
        pt_model=args.pt_model,
        onnx_model=args.onnx_model,
        results_dir=args.results,
        num_runs=args.runs
    )

if __name__ == "__main__":
    main()
