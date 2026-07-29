import os
import argparse
import numpy as np
import cv2
from ultralytics import YOLO
from utils import ensure_dirs

def export_model(
    weights_path: str = "models/best.pt",
    format_type: str = "onnx",
    imgsz: int = 640,
    half: bool = False,
    dynamic: bool = True
) -> str:
    """
    Exports a PyTorch YOLO model (.pt) to ONNX (.onnx) runtime format.
    """
    if not os.path.exists(weights_path):
        raise FileNotFoundError(f"Weights file not found at: {weights_path}")

    print(f"\n==========================================")
    print(f"Exporting Model to {format_type.upper()}")
    print(f"Input Weights: {weights_path}")
    print(f"Resolution: {imgsz}x{imgsz} | Half FP16: {half} | Dynamic Shapes: {dynamic}")
    print(f"==========================================\n")

    model = YOLO(weights_path)
    exported_path = model.export(
        format=format_type,
        imgsz=imgsz,
        half=half,
        dynamic=dynamic
    )

    print(f"Export successfully completed! Output file: {exported_path}")
    
    # Verify ONNX Runtime can load the model if format is ONNX
    if format_type.lower() == "onnx":
        verify_onnx_export(exported_path, imgsz)

    return exported_path

def verify_onnx_export(onnx_path: str, imgsz: int = 640):
    """
    Sanity checks the exported ONNX model using onnxruntime.
    """
    try:
        import onnxruntime as ort
        print("\nRunning ONNX Runtime Sanity Check...")
        session = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])
        
        input_name = session.get_inputs()[0].name
        input_shape = [1, 3, imgsz, imgsz]
        dummy_input = np.random.randn(*input_shape).astype(np.float32)
        
        outputs = session.run(None, {input_name: dummy_input})
        print(f"ONNX Model Verification SUCCESS! Output shape: {outputs[0].shape}")
    except Exception as e:
        print(f"ONNX verification failed or skipped: {e}")

def main():
    parser = argparse.ArgumentParser(description="Export PyTorch YOLO Model to ONNX")
    parser.add_argument("--weights", type=str, default="models/best.pt", help="Path to input PyTorch weights (.pt)")
    parser.add_argument("--format", type=str, default="onnx", help="Export format (e.g. onnx, engine)")
    parser.add_argument("--imgsz", type=int, default=640, help="Image resolution for export")
    parser.add_argument("--half", action="store_true", help="Enable FP16 half precision")
    args = parser.parse_args()

    export_model(
        weights_path=args.weights,
        format_type=args.format,
        imgsz=args.imgsz,
        half=args.half
    )

if __name__ == "__main__":
    main()
