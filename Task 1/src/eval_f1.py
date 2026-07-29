import os
import sys
import glob
import json
import cv2
import numpy as np
import matplotlib.pyplot as plt
import argparse
from typing import Dict, List, Tuple

# Ensure src/ is on sys.path for sibling imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from infer import BallDetector
from utils import compute_iou, xywhn2xyxy, ensure_dirs

def parse_yolo_label(label_path: str, img_width: int, img_height: int) -> List[Tuple[float, float, float, float]]:
    """
    Parses YOLO label text file and converts [class_id, xc, yc, w, h] to [x1, y1, x2, y2] pixels.
    """
    boxes = []
    if not os.path.exists(label_path):
        return boxes

    with open(label_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 5:
                # class_id, xc, yc, w, h
                bbox_norm = np.array([float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])])
                bbox_pixel = xywhn2xyxy(bbox_norm, img_width, img_height)
                boxes.append(bbox_pixel.tolist())

    return boxes

def evaluate_dataset_at_threshold(
    detector: BallDetector,
    images: List[str],
    labels: List[str],
    conf_threshold: float,
    iou_match_threshold: float = 0.5
) -> Tuple[float, float, float]:
    """
    Evaluates True Positives, False Positives, and False Negatives at a specified confidence threshold.
    Returns: (Precision, Recall, F1)
    """
    tp, fp, fn = 0, 0, 0
    detector.conf_thres = conf_threshold

    for img_path, lbl_path in zip(images, labels):
        img = cv2.imread(img_path)
        if img is None:
            continue
        h, w = img.shape[:2]

        gt_boxes = parse_yolo_label(lbl_path, w, h)
        pred_boxes, pred_scores, _ = detector.predict(img)

        matched_gt = [False] * len(gt_boxes)
        matched_pred = [False] * len(pred_boxes)

        for p_idx, p_box in enumerate(pred_boxes):
            best_iou = 0.0
            best_gt_idx = -1

            for g_idx, g_box in enumerate(gt_boxes):
                if matched_gt[g_idx]:
                    continue
                iou = compute_iou(p_box, g_box)
                if iou > best_iou:
                    best_iou = iou
                    best_gt_idx = g_idx

            if best_iou >= iou_match_threshold and best_gt_idx != -1:
                tp += 1
                matched_gt[best_gt_idx] = True
                matched_pred[p_idx] = True
            else:
                fp += 1

        # Any unmatched GT bounding box is a False Negative
        fn += sum(1 for matched in matched_gt if not matched)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return precision, recall, f1

def run_threshold_sweep(
    model_path: str,
    dataset_split_dir: str = "dataset/valid",
    results_dir: str = "results"
) -> Dict[str, Any]:
    """
    Runs confidence threshold sweep from 0.05 to 0.95 and identifies optimal F1 threshold.
    """
    ensure_dirs(results_dir)

    img_dir = os.path.join(dataset_split_dir, "images")
    lbl_dir = os.path.join(dataset_split_dir, "labels")

    image_paths = sorted(
        glob.glob(os.path.join(img_dir, "*.[jJ][pP][gG]")) +
        glob.glob(os.path.join(img_dir, "*.[pP][nN][gG]"))
    )

    label_paths = [
        os.path.join(lbl_dir, os.path.splitext(os.path.basename(p))[0] + ".txt")
        for p in image_paths
    ]

    print(f"\n==========================================")
    print(f"Evaluating Dataset: {dataset_split_dir}")
    print(f"Total Samples: {len(image_paths)}")
    print(f"==========================================\n")

    detector = BallDetector(model_path=model_path, conf_thres=0.1)

    thresholds = np.arange(0.05, 0.95, 0.05)
    precisions, recalls, f1_scores = [], [], []

    best_f1 = -1.0
    best_conf = 0.25
    best_precision = 0.0
    best_recall = 0.0

    for conf in thresholds:
        p, r, f1 = evaluate_dataset_at_threshold(detector, image_paths, label_paths, conf)
        precisions.append(p)
        recalls.append(r)
        f1_scores.append(f1)

        print(f"Conf: {conf:.2f} | Precision: {p:.4f} | Recall: {r:.4f} | F1: {f1:.4f}")

        if f1 > best_f1:
            best_f1 = f1
            best_conf = conf
            best_precision = p
            best_recall = r

    print(f"\nOptimal Confidence Threshold: {best_conf:.2f}")
    print(f"Peak F1 Score: {best_f1:.4f} (Precision: {best_precision:.4f}, Recall: {best_recall:.4f})")

    # Plot F1 vs Threshold curve
    plt.figure(figsize=(9, 5))
    plt.plot(thresholds, precisions, 'b--', label='Precision')
    plt.plot(thresholds, recalls, 'g--', label='Recall')
    plt.plot(thresholds, f1_scores, 'r-', linewidth=2.5, label='F1 Score')
    plt.axvline(best_conf, color='k', linestyle=':', label=f'Optimal Conf ({best_conf:.2f})')
    
    plt.title('VisionBall \u2014 F1 Score vs Confidence Threshold', fontsize=12, fontweight='bold')
    plt.xlabel('Confidence Threshold')
    plt.ylabel('Metric Score')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(loc='lower left')
    
    plot_path = os.path.join(results_dir, "f1_vs_threshold.png")
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"F1 vs Threshold plot saved to: {plot_path}")

    metrics = {
        "model_path": model_path,
        "optimal_confidence_threshold": float(round(best_conf, 2)),
        "max_f1_score": float(round(best_f1, 4)),
        "precision_at_optimal": float(round(best_precision, 4)),
        "recall_at_optimal": float(round(best_recall, 4)),
        "eval_samples": len(image_paths)
    }

    metrics_path = os.path.join(results_dir, "metrics.json")
    
    # Read existing metrics if available to merge
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, 'r') as f:
                existing = json.load(f)
                existing.update(metrics)
                metrics = existing
        except Exception:
            pass

    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=4)
    print(f"Metrics saved to: {metrics_path}")

    return metrics

def main():
    parser = argparse.ArgumentParser(description="Evaluate F1 Score & Perform Confidence Threshold Sweep")
    parser.add_argument("--model", type=str, default="models/best.pt", help="Path to model weights (.pt or .onnx)")
    parser.add_argument("--data_split", type=str, default="dataset/valid", help="Path to evaluation split directory")
    parser.add_argument("--results", type=str, default="results", help="Directory to save evaluation results")
    args = parser.parse_args()

    run_threshold_sweep(
        model_path=args.model,
        dataset_split_dir=args.data_split,
        results_dir=args.results
    )

if __name__ == "__main__":
    main()
