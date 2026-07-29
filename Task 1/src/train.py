import os
import argparse
import shutil
from ultralytics import YOLO
from utils import ensure_dirs, load_yaml_config

def train_ball_detector(
    data_cfg: str = "configs/ball.yaml",
    model_name: str = "yolov8n.pt",
    epochs: int = 15,
    imgsz: int = 640,
    batch: int = 16,
    lr0: float = 0.01,
    patience: int = 10,
    output_dir: str = "models"
) -> str:
    """
    Fine-tune YOLO model on ball dataset and save best weights to output_dir/best.pt.
    """
    ensure_dirs(output_dir)
    print(f"\n==========================================")
    print(f"Starting Ball Detector Training")
    print(f"Base Model: {model_name}")
    print(f"Dataset Config: {data_cfg}")
    print(f"Epochs: {epochs} | Image Size: {imgsz} | Batch Size: {batch}")
    print(f"==========================================\n")

    # Load YOLO model (downloads pretrained weights if not cached)
    model = YOLO(model_name)

    # Train model
    results = model.train(
        data=data_cfg,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        lr0=lr0,
        patience=patience,
        save=True,
        project="runs",
        name="ball_detection",
        exist_ok=True,
        verbose=True
    )

    # Locating best.pt from Ultralytics output
    candidate_paths = [
        os.path.join("runs", "ball_detection", "weights", "best.pt"),
        os.path.join("runs", "detect", "ball_detection", "weights", "best.pt"),
        os.path.join("runs", "detect", "runs", "detect", "ball_detection", "weights", "best.pt"),
    ]
    
    target_best_path = os.path.join(output_dir, "best.pt")
    found_path = None
    for cp in candidate_paths:
        if os.path.exists(cp):
            found_path = cp
            break

    if found_path:
        shutil.copy(found_path, target_best_path)
        print(f"\nTraining Complete! Best model saved to: {target_best_path}")
        return target_best_path
    else:
        print(f"\nWarning: Could not locate best.pt in candidate paths. Check training logs.")
        return ""

def main():
    parser = argparse.ArgumentParser(description="Train YOLO Ball Detection Model")
    parser.add_argument("--data", type=str, default="configs/ball.yaml", help="Path to data YAML config")
    parser.add_argument("--model", type=str, default="yolov8n.pt", help="Pretrained YOLO model (e.g. yolov8n.pt, yolo11n.pt)")
    parser.add_argument("--epochs", type=int, default=15, help="Number of training epochs")
    parser.add_argument("--imgsz", type=int, default=640, help="Image resolution for training")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--lr0", type=float, default=0.01, help="Initial learning rate")
    parser.add_argument("--output", type=str, default="models", help="Output directory for saved model")
    args = parser.parse_args()

    train_ball_detector(
        data_cfg=args.data,
        model_name=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        lr0=args.lr0,
        output_dir=args.output
    )

if __name__ == "__main__":
    main()
