import os
import cv2
import numpy as np
from typing import Tuple, List

try:
    import albumentations as A
    ALBUMENTATIONS_AVAILABLE = True
except ImportError:
    ALBUMENTATIONS_AVAILABLE = False

def get_ball_augmentation_pipeline(imgsz: Tuple[int, int] = (640, 640)):
    """
    Constructs an Albumentations pipeline targeting varied lighting, motion blur, and occlusion.
    """
    if not ALBUMENTATIONS_AVAILABLE:
        print("Warning: albumentations is not installed. Returning identity pipeline.")
        return None

    return A.Compose(
        [
            A.RandomResizedCrop(height=imgsz[0], width=imgsz[1], scale=(0.8, 1.0), p=0.5),
            A.HorizontalFlip(p=0.5),
            A.MotionBlur(blur_limit=(3, 9), p=0.4),
            A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
            A.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1, p=0.4),
            A.GaussNoise(var_limit=(10.0, 50.0), p=0.3),
            A.CoarseDropout(max_holes=4, max_height=32, max_width=32, fill_value=0, p=0.3),
        ],
        bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels'])
    )

def augment_image_and_boxes(
    image: np.ndarray,
    bboxes: List[List[float]],
    class_labels: List[int],
    pipeline=None
) -> Tuple[np.ndarray, List[List[float]], List[int]]:
    """
    Applies the augmentation pipeline to an image and its bounding boxes.
    """
    if pipeline is None:
        return image, bboxes, class_labels

    try:
        transformed = pipeline(image=image, bboxes=bboxes, class_labels=class_labels)
        return transformed['image'], transformed['bboxes'], transformed['class_labels']
    except Exception as e:
        print(f"Augmentation skipped due to error: {e}")
        return image, bboxes, class_labels
