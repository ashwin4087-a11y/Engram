import cv2
import numpy as np
from typing import List, Tuple

class ClassicalBallDetector:
    """
    Classical Computer Vision ball detector using HSV color filtering,
    contour analysis, and Hough Circle Transform as a baseline comparison.
    """
    def __init__(
        self,
        min_radius: int = 5,
        max_radius: int = 100,
        dp: float = 1.2,
        min_dist: int = 30,
        param1: float = 50,
        param2: float = 30
    ):
        self.min_radius = min_radius
        self.max_radius = max_radius
        self.dp = dp
        self.min_dist = min_dist
        self.param1 = param1
        self.param2 = param2

    def detect_hough_circles(self, image: np.ndarray) -> List[Tuple[float, float, float, float]]:
        """
        Detects circular objects using Hough Circle Transform.
        Returns boxes in [x1, y1, x2, y2] format.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)

        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=self.dp,
            minDist=self.min_dist,
            param1=self.param1,
            param2=self.param2,
            minRadius=self.min_radius,
            maxRadius=self.max_radius
        )

        boxes = []
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            # Cap at 50 detections to prevent hanging on noisy images
            for (x, y, r) in circles[:50]:
                x1 = max(0, x - r)
                y1 = max(0, y - r)
                x2 = min(image.shape[1], x + r)
                y2 = min(image.shape[0], y + r)
                boxes.append([float(x1), float(y1), float(x2), float(y2)])

        return boxes

    def detect_color_contours(self, image: np.ndarray) -> List[Tuple[float, float, float, float]]:
        """
        Detects circular motion/objects via HSV color thresholding + circularity filtering.
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Combined mask for vibrant/bright sports ball colors
        lower_mask = cv2.inRange(hsv, np.array([0, 100, 100]), np.array([25, 255, 255]))
        upper_mask = cv2.inRange(hsv, np.array([30, 50, 50]), np.array([90, 255, 255]))
        mask = cv2.bitwise_or(lower_mask, upper_mask)

        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []

        for c in contours:
            area = cv2.contourArea(c)
            if area < (np.pi * (self.min_radius ** 2)):
                continue

            perimeter = cv2.arcLength(c, True)
            if perimeter == 0:
                continue
            circularity = (4 * np.pi * area) / (perimeter ** 2)

            # Circularity thresholding (>0.6 indicates roughly circular object)
            if circularity > 0.55:
                (x, y), radius = cv2.minEnclosingCircle(c)
                if self.min_radius <= radius <= self.max_radius:
                    x1 = max(0, x - radius)
                    y1 = max(0, y - radius)
                    x2 = min(image.shape[1], x + radius)
                    y2 = min(image.shape[0], y + radius)
                    boxes.append([float(x1), float(y1), float(x2), float(y2)])

        return boxes

    def predict(self, image: np.ndarray) -> Tuple[List[Tuple[float, float, float, float]], List[float], List[int]]:
        """
        Predicts ball bounding boxes using combined Hough circles and contour circularity.
        """
        boxes_hough = self.detect_hough_circles(image)
        boxes_color = self.detect_color_contours(image)

        all_boxes = boxes_hough + boxes_color
        scores = [0.75] * len(all_boxes)
        class_ids = [0] * len(all_boxes)
        return all_boxes, scores, class_ids
