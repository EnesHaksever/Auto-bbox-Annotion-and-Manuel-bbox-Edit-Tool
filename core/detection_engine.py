"""Backend detection logic using Ultralytics YOLO.

This module is responsible for loading a YOLO model and running inferences
in a way that's independent of the UI. It handles GPU selection and result
conversion to a unified format.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Tuple

import logging


class DetectionResult:
    """Represents a single detection output."""

    def __init__(self, class_id: int, confidence: float, bbox: Tuple[float, float, float, float]):
        self.class_id = class_id
        self.confidence = confidence
        self.bbox = bbox  # x1, y1, x2, y2

    def to_yolo_format(self, image_size: Tuple[int, int]) -> Tuple[int, float, float, float, float]:
        """Convert the bbox to normalized YOLO format.

        Returns a tuple (class_id, x_center, y_center, width, height) with
        each coordinate in [0,1].
        """
        width, height = image_size
        x1, y1, x2, y2 = self.bbox
        x_center = ((x1 + x2) / 2) / width
        y_center = ((y1 + y2) / 2) / height
        w_norm = (x2 - x1) / width
        h_norm = (y2 - y1) / height
        return (self.class_id, x_center, y_center, w_norm, h_norm)


class DetectionEngine:
    """Wrapper around the Ultralytics YOLO model for inference."""

    def __init__(self, weights_path: Path, confidence: float = 0.25):
        self.weights_path = weights_path
        self.confidence = confidence
        self.model = None  # type: ignore

    def load_model(self) -> None:
        """Load the YOLO model with GPU if available."""
        try:
            from ultralytics import YOLO
        except ImportError as e:
            msg = "ultralytics package is required for detection. Install with: pip install ultralytics"
            logging.error(msg)
            raise RuntimeError(msg) from e

        try:
            device = "cuda" if self._cuda_available() else "cpu"
            logging.info(f"Loading YOLO model from {self.weights_path} on device {device}")
            self.model = YOLO(str(self.weights_path))
            self.model.fuse()  # optional optimizations
            self.model.to(device)
            logging.info("Model loaded successfully")
        except Exception as e:
            msg = f"Failed to load YOLO model: {str(e)}"
            logging.error(msg)
            raise RuntimeError(msg) from e

    def _cuda_available(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def infer_image(self, image_path: Path) -> Iterable[DetectionResult]:
        """Run inference on a single image and yield results."""
        if self.model is None:
            raise RuntimeError("Model not loaded")

        results = self.model(str(image_path), conf=self.confidence)
        for r in results:
            for box in r.boxes:
                class_id = int(box.cls.item())
                conf = float(box.conf.item())
                # xyxy format: [x1, y1, x2, y2]
                coords = box.xyxy[0].tolist()
                x1, y1, x2, y2 = coords[0], coords[1], coords[2], coords[3]
                yield DetectionResult(class_id, conf, (x1, y1, x2, y2))


# additional helper functions could go here
