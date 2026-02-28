"""Utilities for reading and writing YOLO-format label files."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple


def read_yolo_labels(label_path: Path) -> List[Tuple[int, float, float, float, float]]:
    """Read a YOLO label file and return a list of entries.

    Each entry is (class_id, x_center, y_center, width, height) with values in
    normalized [0,1] coordinates.
    """
    entries: List[Tuple[int, float, float, float, float]] = []
    with label_path.open("r") as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            class_id = int(parts[0])
            coords = tuple(float(x) for x in parts[1:])
            entries.append((class_id, *coords))
    return entries


def write_yolo_labels(label_path: Path, entries: List[Tuple[int, float, float, float, float]]) -> None:
    """Write a list of YOLO label entries to a file, overwriting if necessary."""
    with label_path.open("w") as f:
        for entry in entries:
            f.write(" ".join(str(x) for x in entry) + "\n")
