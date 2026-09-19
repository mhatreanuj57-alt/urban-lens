"""YOLO detector for UrbanLens inference."""

from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


class UrbanLensDetector:
    """Run YOLO detection on images."""

    def __init__(self, model_path: str, device: str = "cpu", conf: float = 0.25):
        """
        Initialize detector.

        Args:
            model_path: Path to YOLO weights (.pt file)
            device: 'cpu' or 'cuda'
            conf: Confidence threshold
        """
        try:
            from ultralytics import YOLO
        except ImportError:
            raise ImportError("Install ultralytics: pip install ultralytics")

        self.model = YOLO(model_path)
        self.device = device
        self.conf = conf

    def detect(self, image: np.ndarray | str | Path) -> list[dict[str, Any]]:
        """
        Run detection on an image.

        Args:
            image: numpy array, file path, or PIL Image

        Returns:
            List of detections with keys:
                - bbox: [x1, y1, x2, y2]
                - class_id: int
                - class_name: str
                - confidence: float
        """
        results = self.model(image, device=self.device, conf=self.conf)
        detections = []

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for box in boxes:
                detections.append({
                    "bbox": box.xyxy[0].tolist(),
                    "class_id": int(box.cls[0]),
                    "class_name": result.names[int(box.cls[0])],
                    "confidence": float(box.conf[0]),
                })

        return detections

    def detect_batch(
        self, images: list[np.ndarray | str | Path]
    ) -> list[list[dict[str, Any]]]:
        """Run detection on a batch of images."""
        return [self.detect(img) for img in images]
