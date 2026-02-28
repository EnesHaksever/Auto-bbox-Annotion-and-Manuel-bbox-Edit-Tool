"""Side panel containing controls for both modes."""

from __future__ import annotations

from PyQt6 import QtWidgets


class ControlPanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QtWidgets.QVBoxLayout(self)

        # placeholder widgets for file selection, thresholds, etc.
        # they will be populated by specific mode controllers
