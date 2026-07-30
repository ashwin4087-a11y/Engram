import os
import sys
import time
import cv2
import numpy as np
from typing import List, Tuple, Union, Dict, Any

# Ensure src/ is on sys.path for sibling imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import letterbox, compute_iou

class BallDetector:
    """
    Unified Ball Detection Engine supporting PyTorch (.pt) and ONNX (.onnx) backends.
    """
    def __init__(
        self,
        model_path: str = "models/best.pt",
        conf_thres: float = 0.25,
        iou_thres: float = 0.45,
        imgsz: int = 640,
        device: str = "auto"
    ):
        self.model_path = model_path
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres
        self.imgsz = imgsz
        self.device = device
        self.backend = "unknown"

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Detector weights file not found: {model_path}")

        if model_path.endswith(".onnx"):
            self._init_onnx()
        elif model_path.endswith(".pt"):
            self._init_pytorch()
        else:
            raise ValueError(f"Unsupported model extension: {model_path}. Expected .pt or .onnx")

    def _init_pytorch(self):
        from ultralytics import YOLO
        self.backend = "pytorch"
        self.model = YOLO(self.model_path)
        print(f"[BallDetector] Initialized PyTorch backend with model: {self.model_path}")

    def _init_onnx(self):
        import onnxruntime as ort
        self.backend = "onnx"
        
        providers = ['CPUExecutionProvider']
        if self.device != 'cpu':
            available_providers = ort.get_available_providers()
            if 'CUDAExecutionProvider' in available_providers:
                providers.insert(0, 'CUDAExecutionProvider')
                
        self.session = ort.InferenceSession(self.model_path, providers=providers)
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        print(f"[BallDetector] Initialized ONNX backend with providers: {self.session.get_providers()}")

    def predict(self, image: np.ndarray, conf_thres: float = None, iou_thres: float = None) -> Tuple[List[Tuple[float, float, float, float]], List[float], List[int]]:
        """
        Runs detection on an OpenCV BGR image frame.
        Returns:
            boxes: List of [x1, y1, x2, y2] in original image pixel coordinates
            scores: List of confidence floats
            class_ids: List of integer class IDs (0 for ball)
        """
        conf = conf_thres if conf_thres is not None else self.conf_thres
        iou = iou_thres if iou_thres is not None else self.iou_thres

        if self.backend == "pytorch":
            return self._predict_pytorch(image, conf, iou)
        elif self.backend == "onnx":
            return self._predict_onnx(image, conf, iou)
        else:
            return [], [], []

    def _predict_pytorch(self, image: np.ndarray, conf_thres: float, iou_thres: float):
        results = self.model.predict(
            source=image,
            conf=conf_thres,
            iou=iou_thres,
            imgsz=self.imgsz,
            verbose=False
        )

        boxes, scores, class_ids = [], [], []
        if len(results) > 0 and results[0].boxes is not None:
            res_boxes = results[0].boxes
            for i in range(len(res_boxes)):
                box = res_boxes.xyxy[i].cpu().numpy().tolist()
                score = float(res_boxes.conf[i].cpu().numpy())
                cls_id = int(res_boxes.cls[i].cpu().numpy())
                boxes.append(box)
                scores.append(score)
                class_ids.append(cls_id)

        return boxes, scores, class_ids

    def _predict_onnx(self, image: np.ndarray, conf_thres: float, iou_thres: float):
        orig_h, orig_w = image.shape[:2]
        padded_img, (ratio_w, ratio_h), (pad_w, pad_h) = letterbox(image, (self.imgsz, self.imgsz))

        # Preprocessing: BGR -> RGB, HWC -> CHW, normalize 0..1
        blob = cv2.cvtColor(padded_img, cv2.COLOR_BGR2RGB)
        blob = blob.transpose((2, 0, 1)).astype(np.float32) / 255.0
        blob = np.expand_dims(blob, axis=0)

        # Run ONNX session
        outputs = self.session.run([self.output_name], {self.input_name: blob})[0]
        
        # YOLOv8 ONNX output shape is usually [1, 5, 8400] (cx, cy, w, h, score)
        predictions = np.squeeze(outputs, axis=0)
        if predictions.shape[0] < predictions.shape[1]:
            predictions = predictions.T  # Transpose to [N, 5]

        boxes_raw, scores_raw = [], []
        for pred in predictions:
            cx, cy, w, h = pred[0:4]
            # Handle single class or multi-class confidences
            score = float(pred[4]) if len(pred) == 5 else float(np.max(pred[4:]))
            
            if score >= conf_thres:
                x1 = (cx - w / 2 - pad_w) / ratio_w
                y1 = (cy - h / 2 - pad_h) / ratio_h
                x2 = (cx + w / 2 - pad_w) / ratio_w
                y2 = (cy + h / 2 - pad_h) / ratio_h

                # Clip to image boundaries
                x1 = max(0, min(orig_w, x1))
                y1 = max(0, min(orig_h, y1))
                x2 = max(0, min(orig_w, x2))
                y2 = max(0, min(orig_h, y2))

                boxes_raw.append([x1, y1, x2, y2])
                scores_raw.append(score)

        # Perform NMS
        final_boxes, final_scores, final_cls = [], [], []
        if len(boxes_raw) > 0:
            indices = cv2.dnn.NMSBoxes(
                bboxes=boxes_raw,
                scores=scores_raw,
                score_threshold=conf_thres,
                nms_threshold=iou_thres
            )

            if len(indices) > 0:
                for idx in indices.flatten():
                    final_boxes.append(boxes_raw[idx])
                    final_scores.append(scores_raw[idx])
                    final_cls.append(0)

        return final_boxes, final_scores, final_cls


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Test Ball Detector Inference Engine")
    parser.add_argument("--model", type=str, default="models/best.pt", help="Path to .pt or .onnx model")
    parser.add_argument("--image", type=str, required=True, help="Path to input test image")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    args = parser.parse_args()

    detector = BallDetector(model_path=args.model, conf_thres=args.conf)
    image = cv2.imread(args.image)
    if image is None:
        print(f"Error: Could not read image at {args.image}")
        return

    start_t = time.perf_counter()
    boxes, scores, class_ids = detector.predict(image)
    latency_ms = (time.perf_counter() - start_t) * 1000.0

    print(f"\nInference completed in {latency_ms:.2f} ms")
    print(f"Detected {len(boxes)} ball(s):")
    for box, score in zip(boxes, scores):
        print(f"  - Box: {[round(c, 1) for c in box]} | Conf: {score:.3f}")

if __name__ == "__main__":
    main()
