import os
import cv2
import yaml
import numpy as np
from typing import List, Tuple, Dict, Any, Union

def ensure_dirs(*paths: str) -> None:
    """Ensure that all provided directory paths exist."""
    for path in paths:
        if path:
            os.makedirs(path, exist_ok=True)

def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """Safely load a YAML configuration file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def compute_iou(box1: Tuple[float, float, float, float], box2: Tuple[float, float, float, float]) -> float:
    """
    Compute Intersection over Union (IoU) between two bounding boxes.
    Format: [x1, y1, x2, y2]
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection_area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    if intersection_area == 0.0:
        return 0.0

    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union_area = box1_area + box2_area - intersection_area

    if union_area <= 0.0:
        return 0.0
    return intersection_area / union_area

def xywhn2xyxy(x: np.ndarray, w: int, h: int) -> np.ndarray:
    """
    Convert normalized [xc, yc, w, h] to pixel coordinates [x1, y1, x2, y2].
    """
    y = np.zeros_like(x)
    y[..., 0] = (x[..., 0] - x[..., 2] / 2) * w  # x1
    y[..., 1] = (x[..., 1] - x[..., 3] / 2) * h  # y1
    y[..., 2] = (x[..., 0] + x[..., 2] / 2) * w  # x2
    y[..., 3] = (x[..., 1] + x[..., 3] / 2) * h  # y2
    return y

def xyxy2xywhn(x: np.ndarray, w: int, h: int) -> np.ndarray:
    """
    Convert pixel coordinates [x1, y1, x2, y2] to normalized [xc, yc, w, h].
    """
    y = np.zeros_like(x, dtype=np.float32)
    y[..., 0] = ((x[..., 0] + x[..., 2]) / 2) / w  # xc
    y[..., 1] = ((x[..., 1] + x[..., 3]) / 2) / h  # yc
    y[..., 2] = (x[..., 2] - x[..., 0]) / w        # w
    y[..., 3] = (x[..., 3] - x[..., 1]) / h        # h
    return y

def letterbox(
    img: np.ndarray,
    new_shape: Tuple[int, int] = (640, 640),
    color: Tuple[int, int, int] = (114, 114, 114),
    auto: bool = False,
    scaleFill: bool = False,
    scaleup: bool = True,
    stride: int = 32
) -> Tuple[np.ndarray, Tuple[float, float], Tuple[int, int]]:
    """
    Resize image to a target shape with padding, preserving aspect ratio.
    Returns: (padded_img, (ratio_w, ratio_h), (pad_w, pad_h))
    """
    shape = img.shape[:2]  # current shape [height, width]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    if not scaleup:
        r = min(r, 1.0)

    # Compute padding
    ratio = (r, r)
    new_unpad = (int(round(shape[1] * r)), int(round(shape[0] * r)))
    dw = new_shape[1] - new_unpad[0]
    dh = new_shape[0] - new_unpad[1]

    if auto:
        dw, dh = np.mod(dw, stride), np.mod(dh, stride)
    elif scaleFill:
        dw, dh = 0.0, 0.0
        new_unpad = (new_shape[1], new_shape[0])
        ratio = (new_shape[1] / shape[1], new_shape[0] / shape[0])

    dw /= 2
    dh /= 2

    if shape[::-1] != new_unpad:
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return img, ratio, (left, top)

def draw_detections(
    image: np.ndarray,
    boxes: List[Tuple[float, float, float, float]],
    scores: List[float],
    class_ids: List[int] = None,
    class_names: List[str] = None,
    fps: float = None,
    color: Tuple[int, int, int] = (0, 255, 0)
) -> np.ndarray:
    """
    Draw bounding boxes, confidence scores, and live FPS info on the input frame.
    """
    img = image.copy()
    if class_names is None:
        class_names = ["ball"]

    for idx, (box, score) in enumerate(zip(boxes, scores)):
        x1, y1, x2, y2 = map(int, box)
        cid = class_ids[idx] if class_ids is not None and idx < len(class_ids) else 0
        label_text = f"{class_names[cid]}: {score:.2f}" if cid < len(class_names) else f"ball: {score:.2f}"

        # Draw bounding box
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

        # Draw label background box
        (tw, th), baseline = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(img, (x1, max(0, y1 - th - baseline - 4)), (x1 + tw + 6, max(th + 4, y1)), color, -1)
        cv2.putText(
            img, label_text, (x1 + 3, max(y1 - 4, th + 2)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA
        )

    if fps is not None:
        fps_text = f"FPS: {fps:.1f}"
        cv2.putText(
            img, fps_text, (15, 35),
            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2, cv2.LINE_AA
        )

    return img
