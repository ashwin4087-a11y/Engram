import os
import sys
import glob
import cv2
import numpy as np
import argparse
from typing import Dict, List, Tuple

# Ensure src/ is on sys.path for sibling imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import ensure_dirs, load_yaml_config

def validate_dataset(dataset_dir: str) -> Dict[str, int]:
    """
    Scans the train, valid, and test split directories and returns file count metrics.
    """
    stats = {}
    splits = ['train', 'valid', 'test']
    
    for split in splits:
        img_dir = os.path.join(dataset_dir, split, 'images')
        lbl_dir = os.path.join(dataset_dir, split, 'labels')
        
        images = glob.glob(os.path.join(img_dir, '*.[jJ][pP][gG]')) + \
                 glob.glob(os.path.join(img_dir, '*.[pP][nN][gG]')) + \
                 glob.glob(os.path.join(img_dir, '*.[jJ][pP][eE][gG]'))
        labels = glob.glob(os.path.join(lbl_dir, '*.txt')) if os.path.exists(lbl_dir) else []
        
        stats[f"{split}_images"] = len(images)
        stats[f"{split}_labels"] = len(labels)
        
    return stats

def generate_synthetic_ball_data(output_dir: str, num_samples: int = 50, split: str = 'train') -> None:
    """
    Generates synthetic ball images with YOLO labels for de-risking and pipeline testing.
    """
    img_dir = os.path.join(output_dir, split, 'images')
    lbl_dir = os.path.join(output_dir, split, 'labels')
    ensure_dirs(img_dir, lbl_dir)

    for i in range(num_samples):
        # Create random background
        h, w = 480, 640
        bg_color = np.random.randint(50, 200, size=(3,), dtype=np.uint8)
        img = np.full((h, w, 3), bg_color, dtype=np.uint8)

        # Draw ball
        r = np.random.randint(15, 50)
        cx = np.random.randint(r + 10, w - r - 10)
        cy = np.random.randint(r + 10, h - r - 10)
        ball_color = (
            int(np.random.randint(0, 255)),
            int(np.random.randint(0, 255)),
            int(np.random.randint(0, 255))
        )
        cv2.circle(img, (cx, cy), r, ball_color, -1)
        # Add highlight circle for 3D sphere look
        cv2.circle(img, (cx - r // 3, cy - r // 3), max(2, r // 4), (255, 255, 255), -1)

        # Save image
        filename = f"synthetic_ball_{split}_{i:04d}"
        img_path = os.path.join(img_dir, f"{filename}.jpg")
        cv2.imwrite(img_path, img)

        # Compute YOLO normalized bbox [xc, yc, w, h]
        xc_norm = cx / w
        yc_norm = cy / h
        w_norm = (2 * r) / w
        h_norm = (2 * r) / h

        # Save YOLO label
        lbl_path = os.path.join(lbl_dir, f"{filename}.txt")
        with open(lbl_path, 'w') as f:
            f.write(f"0 {xc_norm:.6f} {yc_norm:.6f} {w_norm:.6f} {h_norm:.6f}\n")

    print(f"Generated {num_samples} synthetic images and labels in {split} split.")

def main():
    parser = argparse.ArgumentParser(description="Dataset Preparation & Integrity Verification")
    parser.add_argument("--config", type=str, default="configs/ball.yaml", help="Path to dataset config YAML")
    parser.add_argument("--synthetic", action="store_true", help="Generate synthetic test dataset")
    args = parser.parse_args()

    config = load_yaml_config(args.config)
    dataset_dir = config.get('path', './dataset')

    if args.synthetic:
        print("Generating synthetic ball dataset for pipeline testing...")
        generate_synthetic_ball_data(dataset_dir, num_samples=30, split='train')
        generate_synthetic_ball_data(dataset_dir, num_samples=10, split='valid')
        generate_synthetic_ball_data(dataset_dir, num_samples=10, split='test')

    print("\n--- Dataset Summary ---")
    stats = validate_dataset(dataset_dir)
    for key, count in stats.items():
        print(f"  {key}: {count}")

if __name__ == "__main__":
    main()
