"""Widget responsible for displaying an image and handling pan/zoom and bbox interaction."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple

from PyQt6 import QtCore, QtGui, QtWidgets

from core.bbox_model import BoundingBox


class CanvasMode(Enum):
    """Canvas interaction modes."""
    NAVIGATE = "navigate"  # pan/zoom only
    MARK = "mark"  # draw new boxes
    SELECT = "select"  # select and edit existing boxes


class CanvasWidget(QtWidgets.QWidget):
    boxes_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap: Optional[QtGui.QPixmap] = None
        self._scale = 1.0
        self._offset = QtCore.QPointF(0, 0)
        self._boxes: List[BoundingBox] = []
        self._selected_box: Optional[BoundingBox] = None
        self._mode = CanvasMode.NAVIGATE
        self.new_box_class: int = 0

        # drag/draw state
        self._dragging = False
        self._drag_start = QtCore.QPointF(0, 0)
        self._current_rect: Optional[QtCore.QRectF] = None

        # pan state
        self._panning = False
        self._pan_start: QtCore.QPoint = QtCore.QPoint(0, 0)

        # resize handle state
        self._resizing = False
        self._resize_handle = None  # which corner/edge: 'tl', 'tr', 'bl', 'br', 'l', 'r', 't', 'b'
        self._handle_size = 8

        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

    def set_mode(self, mode: CanvasMode) -> None:
        """Switch interaction mode."""
        self._mode = mode
        self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)

    def load_image(self, path: Path) -> None:
        self._pixmap = QtGui.QPixmap(str(path))
        self._scale = 1.0
        self._offset = QtCore.QPointF(0, 0)
        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        if self._pixmap:
            # draw image with current transform
            painter.save()
            painter.translate(self._offset)
            painter.scale(self._scale, self._scale)
            painter.drawPixmap(0, 0, self._pixmap)
            painter.restore()

        # draw bboxes WITH transform applied so they scale with image
        painter.save()
        painter.translate(self._offset)
        painter.scale(self._scale, self._scale)
        
        for box in self._boxes:
            rect = QtCore.QRectF(box.x1, box.y1, box.width(), box.height())
            # a couple pixels thicker makes boxes easier to see
            if box is self._selected_box:
                pen = QtGui.QPen(QtGui.QColor("red"), 3 / self._scale)
            else:
                pen = QtGui.QPen(QtGui.QColor("green"), 2 / self._scale)
            painter.setPen(pen)
            painter.drawRect(rect)
            
            # draw resize handles if selected
            if box is self._selected_box and self._mode == CanvasMode.SELECT:
                handle_size_transformed = self._handle_size / self._scale
                handle_brush = QtGui.QBrush(QtGui.QColor("red"))
                # corners
                painter.fillRect(QtCore.QRectF(box.x1 - handle_size_transformed/2, box.y1 - handle_size_transformed/2, handle_size_transformed, handle_size_transformed), handle_brush)
                painter.fillRect(QtCore.QRectF(box.x2 - handle_size_transformed/2, box.y1 - handle_size_transformed/2, handle_size_transformed, handle_size_transformed), handle_brush)
                painter.fillRect(QtCore.QRectF(box.x1 - handle_size_transformed/2, box.y2 - handle_size_transformed/2, handle_size_transformed, handle_size_transformed), handle_brush)
                painter.fillRect(QtCore.QRectF(box.x2 - handle_size_transformed/2, box.y2 - handle_size_transformed/2, handle_size_transformed, handle_size_transformed), handle_brush)

        # draw rectangle being created (in MARK mode)
        if self._current_rect and self._mode == CanvasMode.MARK:
            painter.setPen(QtGui.QPen(QtGui.QColor("blue"), 1 / self._scale, QtCore.Qt.PenStyle.DashLine))
            painter.drawRect(self._current_rect)
        
        painter.restore()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._mode == CanvasMode.NAVIGATE:
            # allow both middle-button and left-button drag to pan the image
            if event.button() in (QtCore.Qt.MouseButton.MiddleButton, QtCore.Qt.MouseButton.LeftButton):
                self._panning = True
                self._pan_start = event.pos()
        
        elif self._mode == CanvasMode.MARK:
            if event.button() == QtCore.Qt.MouseButton.LeftButton:
                pos = self._to_image_coords(event.position())
                self._dragging = True
                self._drag_start = pos
                self._current_rect = QtCore.QRectF(pos, pos)
        
        elif self._mode == CanvasMode.SELECT:
            if event.button() == QtCore.Qt.MouseButton.LeftButton:
                pos = self._to_image_coords(event.position())
                # check if clicking on a handle
                if self._selected_box:
                    handle = self._get_handle_at(pos, self._selected_box)
                    if handle:
                        self._resizing = True
                        self._resize_handle = handle
                        return
                
                # otherwise try to select a box
                self._selected_box = None
                for box in self._boxes:
                    rect = QtCore.QRectF(box.x1, box.y1, box.width(), box.height())
                    if rect.contains(pos):
                        self._selected_box = box
                        self._dragging = True
                        self._drag_start = pos
                        break
                self.boxes_changed.emit()
                self.update()
            
            elif event.button() == QtCore.Qt.MouseButton.MiddleButton:
                self._panning = True
                self._pan_start = event.pos()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._mode == CanvasMode.NAVIGATE:
            if self._panning:
                delta = event.pos() - self._pan_start
                self._offset += QtCore.QPointF(delta)
                self._pan_start = event.pos()
                self.update()
        
        elif self._mode == CanvasMode.MARK:
            if self._dragging and self._current_rect is not None:
                pos = self._to_image_coords(event.position())
                self._current_rect.setBottomRight(pos)
                self.update()
        
        elif self._mode == CanvasMode.SELECT:
            if self._resizing and self._selected_box and self._resize_handle:
                pos = self._to_image_coords(event.position())
                self._resize_box(self._selected_box, self._resize_handle, pos)
                self.boxes_changed.emit()
                self.update()
            elif self._dragging and self._selected_box:
                delta = self._to_image_coords(event.position()) - self._drag_start
                self._selected_box.x1 += delta.x()
                self._selected_box.y1 += delta.y()
                self._selected_box.x2 += delta.x()
                self._selected_box.y2 += delta.y()
                self._drag_start = self._to_image_coords(event.position())
                self.boxes_changed.emit()
                self.update()
            elif self._panning:
                delta = event.pos() - self._pan_start
                self._offset += QtCore.QPointF(delta)
                self._pan_start = event.pos()
                self.update()
            else:
                pos = self._to_image_coords(event.position())
                if self._selected_box and self._get_handle_at(pos, self._selected_box):
                    self.setCursor(QtCore.Qt.CursorShape.SizeAllCursor)
                else:
                    self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            if self._mode == CanvasMode.MARK and self._dragging:
                self._dragging = False
                if self._current_rect is not None:
                    rect = self._current_rect.normalized()
                    self._boxes.append(BoundingBox(0, rect.left(), rect.top(), rect.right(), rect.bottom()))
                    self._current_rect = None
                    self.update()
            elif self._mode == CanvasMode.SELECT:
                self._dragging = False
                self._resizing = False
                self._resize_handle = None
            # also stop panning if left-button was used for panning
            if self._panning:
                self._panning = False
        elif event.button() == QtCore.Qt.MouseButton.MiddleButton:
            if self._panning:
                self._panning = False

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        """Zoom in/out."""
        if self._mode in [CanvasMode.NAVIGATE, CanvasMode.SELECT]:
            delta = event.angleDelta().y()
            factor = 1.0 + (delta / 1200)
            old_pos = self._to_image_coords(event.position())
            self._scale *= factor
            self._scale = max(0.1, min(self._scale, 10.0))  # clamp
            new_pos = self._to_image_coords(event.position())
            self._offset += (new_pos - old_pos) * self._scale
            self.update()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Handle Delete key to remove selected box."""
        if event.key() == QtCore.Qt.Key.Key_Delete and self._selected_box:
            if self._selected_box in self._boxes:
                self._boxes.remove(self._selected_box)
            self._selected_box = None
            self.boxes_changed.emit()
            self.update()

    def _get_handle_at(self, pos: QtCore.QPointF, box: BoundingBox) -> Optional[str]:
        """Check if pos is near a resize handle. Returns handle name or None."""
        threshold = self._handle_size / self._scale
        x, y = pos.x(), pos.y()
        
        # corners
        if abs(x - box.x1) < threshold and abs(y - box.y1) < threshold:
            return "tl"
        if abs(x - box.x2) < threshold and abs(y - box.y1) < threshold:
            return "tr"
        if abs(x - box.x1) < threshold and abs(y - box.y2) < threshold:
            return "bl"
        if abs(x - box.x2) < threshold and abs(y - box.y2) < threshold:
            return "br"
        
        # edges
        if abs(x - box.x1) < threshold and box.y1 <= y <= box.y2:
            return "l"
        if abs(x - box.x2) < threshold and box.y1 <= y <= box.y2:
            return "r"
        if abs(y - box.y1) < threshold and box.x1 <= x <= box.x2:
            return "t"
        if abs(y - box.y2) < threshold and box.x1 <= x <= box.x2:
            return "b"
        
        return None

    def _resize_box(self, box: BoundingBox, handle: str, new_pos: QtCore.QPointF) -> None:
        """Resize box based on which handle is being dragged."""
        if handle == "tl":
            box.x1 = new_pos.x()
            box.y1 = new_pos.y()
        elif handle == "tr":
            box.x2 = new_pos.x()
            box.y1 = new_pos.y()
        elif handle == "bl":
            box.x1 = new_pos.x()
            box.y2 = new_pos.y()
        elif handle == "br":
            box.x2 = new_pos.x()
            box.y2 = new_pos.y()
        elif handle == "l":
            box.x1 = new_pos.x()
        elif handle == "r":
            box.x2 = new_pos.x()
        elif handle == "t":
            box.y1 = new_pos.y()
        elif handle == "b":
            box.y2 = new_pos.y()

    def _to_image_coords(self, point: QtCore.QPointF) -> QtCore.QPointF:
        """Convert widget coordinates to image coordinates."""
        x = (point.x() - self._offset.x()) / self._scale
        y = (point.y() - self._offset.y()) / self._scale
        return QtCore.QPointF(x, y)
