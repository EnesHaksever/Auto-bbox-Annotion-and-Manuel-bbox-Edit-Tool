"""A simple data model for bounding boxes and collections thereof."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class BoundingBox:
    """Represents a bounding box in image coordinates."""
    class_id: int
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float | None = None

    def width(self) -> float:
        return self.x2 - self.x1

    def height(self) -> float:
        return self.y2 - self.y1

    def to_tuple(self) -> Tuple[float, float, float, float]:
        return (self.x1, self.y1, self.x2, self.y2)


@dataclass
class Annotation:
    """Holds a list of bounding boxes for a single image."""
    boxes: List[BoundingBox] = field(default_factory=list)

    def add(self, box: BoundingBox) -> None:
        self.boxes.append(box)

    def remove(self, box: BoundingBox) -> None:
        self.boxes.remove(box)

    def clear(self) -> None:
        self.boxes.clear()
