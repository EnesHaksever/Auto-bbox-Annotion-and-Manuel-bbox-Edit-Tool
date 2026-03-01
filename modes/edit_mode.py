"""Widget and logic for manual bounding box editing mode."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PyQt6 import QtWidgets

from ui.canvas_widget import CanvasWidget, CanvasMode
from ui.control_panel import ControlPanel

from core.bbox_model import Annotation, BoundingBox
from core.yolo_label_parser import read_yolo_labels, write_yolo_labels


class EditMode(QtWidgets.QWidget):
    """Container for image navigation and bounding box editing."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QtWidgets.QVBoxLayout(self)

        # top row: file/label selectors
        top_bar = QtWidgets.QHBoxLayout()
        self._image_dir_edit = QtWidgets.QLineEdit()
        btn1 = QtWidgets.QPushButton("Gözat...")
        top_bar.addWidget(QtWidgets.QLabel("Fotolar:"))
        top_bar.addWidget(self._image_dir_edit)
        top_bar.addWidget(btn1)
        btn1.clicked.connect(self._choose_images)

        self._label_dir_edit = QtWidgets.QLineEdit()
        btn2 = QtWidgets.QPushButton("Gözat...")
        top_bar.addWidget(QtWidgets.QLabel("Etiketler:"))
        top_bar.addWidget(self._label_dir_edit)
        top_bar.addWidget(btn2)
        btn2.clicked.connect(self._choose_labels)

        self._layout.addLayout(top_bar)

        # main content area
        content = QtWidgets.QHBoxLayout()
        self._layout.addLayout(content)

        # LEFT PANEL: modes, class, nav, save, list
        left_panel = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_panel)

        left_layout.addWidget(QtWidgets.QLabel("Canvas Mode:"))
        self.navigate_btn = QtWidgets.QPushButton("Gezinme\n(Pan/Zoom)")
        self.navigate_btn.setCheckable(True)
        self.navigate_btn.setChecked(True)
        self.mark_btn = QtWidgets.QPushButton("İşaretleme\n(Bbox Çiz)")
        self.mark_btn.setCheckable(True)
        self.select_btn = QtWidgets.QPushButton("Seçme/Düzenleme\n(Taşı, Resize, Sil)")
        self.select_btn.setCheckable(True)
        for btn in [self.navigate_btn, self.mark_btn, self.select_btn]:
            left_layout.addWidget(btn)
        self.navigate_btn.clicked.connect(lambda: self._set_mode(CanvasMode.NAVIGATE))
        self.mark_btn.clicked.connect(lambda: self._set_mode(CanvasMode.MARK))
        self.select_btn.clicked.connect(lambda: self._set_mode(CanvasMode.SELECT))

        left_layout.addSpacing(10)
        left_layout.addWidget(QtWidgets.QLabel("Class ID:"))
        self.class_spin = QtWidgets.QSpinBox()
        self.class_spin.setRange(0, 999)
        left_layout.addWidget(self.class_spin)

        left_layout.addSpacing(10)
        left_layout.addWidget(QtWidgets.QLabel("Gezinti:"))
        self.prev_button = QtWidgets.QPushButton("◀ Önceki")
        self.next_button = QtWidgets.QPushButton("Sonraki ▶")
        left_layout.addWidget(self.prev_button)
        left_layout.addWidget(self.next_button)
        self.index_label = QtWidgets.QLabel("0 / 0")
        left_layout.addWidget(self.index_label)

        # direct-jump control: enter index and go
        jump_row = QtWidgets.QHBoxLayout()
        jump_row.addWidget(QtWidgets.QLabel("Git: "))
        self.goto_spin = QtWidgets.QSpinBox()
        self.goto_spin.setRange(1, 1)
        self.goto_spin.setEnabled(False)
        jump_row.addWidget(self.goto_spin)
        self.goto_button = QtWidgets.QPushButton("Git")
        self.goto_button.setEnabled(False)
        jump_row.addWidget(self.goto_button)
        left_layout.addLayout(jump_row)

        left_layout.addSpacing(10)
        self.save_button = QtWidgets.QPushButton("💾 Kaydet")
        left_layout.addWidget(self.save_button)

        left_layout.addSpacing(10)
        left_layout.addWidget(QtWidgets.QLabel("Kutular:"))
        self.box_list = QtWidgets.QListWidget()
        left_layout.addWidget(self.box_list)

        # saved images list below the box list
        left_layout.addSpacing(10)
        left_layout.addWidget(QtWidgets.QLabel("Kaydedilenler:"))
        self.saved_list = QtWidgets.QListWidget()
        left_layout.addWidget(self.saved_list)
        self.saved_count_label = QtWidgets.QLabel("Toplam: 0")
        left_layout.addWidget(self.saved_count_label)

        left_layout.addStretch()

        # delete current image + label
        left_layout.addSpacing(6)
        self.delete_button = QtWidgets.QPushButton("Fotoğrafı Sil")
        left_layout.addWidget(self.delete_button)

        content.addWidget(left_panel, 0)

        # RIGHT PANEL: only canvas
        self.canvas = CanvasWidget()
        self.canvas.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.canvas.setMinimumSize(200, 200)
        content.addWidget(self.canvas, 1)

        # connections
        self.prev_button.clicked.connect(self.prev_image)
        self.next_button.clicked.connect(self.next_image)
        self.goto_button.clicked.connect(self.go_to_image)
        # connect delete
        self.delete_button.clicked.connect(self.delete_current_image)
        self.save_button.clicked.connect(self.save_current_annotation)
        self.canvas.boxes_changed.connect(self._on_boxes_changed)
        self.box_list.itemClicked.connect(self._box_list_selected)
        self.class_spin.valueChanged.connect(lambda v: setattr(self.canvas, 'new_box_class', v))
        self.class_spin.valueChanged.connect(self._change_selected_class)

        # annotation store & state
        self.annotations: dict[Path, Annotation] = {}
        self.dirty: dict[Path, bool] = {}
        self.annotation = Annotation()
        self.images: List[Path] = []
        self.current_index: int = -1

        # annotation state
        self.annotation = Annotation()
        self.images: List[Path] = []
        self.current_index: int = -1
        # keep list of boxes updated

    def _show_temporary_message(self, text: str, timeout: int = 1500) -> None:
        """Display a transient tooltip-style message at bottom-right of widget."""
        # map bottom-right corner of this widget to global coords
        pos = self.mapToGlobal(self.rect().bottomRight())
        QtWidgets.QToolTip.showText(pos, text, self, self.rect(), timeout)

        
    def _refresh_box_list(self) -> None:
        sel_idx = -1
        if self.canvas._selected_box in self.canvas._boxes:
            sel_idx = self.canvas._boxes.index(self.canvas._selected_box)
        self.box_list.clear()
        for box in self.canvas._boxes:
            self.box_list.addItem(f"class {box.class_id}: [{box.x1:.1f},{box.y1:.1f},{box.x2:.1f},{box.y2:.1f}]")
        if sel_idx >= 0 and sel_idx < self.box_list.count():
            self.box_list.setCurrentRow(sel_idx)
        # mark dirty because list reflects change
        self._mark_dirty()

    def _change_selected_class(self, value: int) -> None:
        if self.canvas._selected_box:
            self.canvas._selected_box.class_id = value
            self.canvas.boxes_changed.emit()

    def _box_list_selected(self, item: QtWidgets.QListWidgetItem) -> None:
        idx = self.box_list.row(item)
        if 0 <= idx < len(self.canvas._boxes):
            self.canvas._selected_box = self.canvas._boxes[idx]
            self.class_spin.setValue(self.canvas._selected_box.class_id)
            self.canvas.update()

    def _on_boxes_changed(self) -> None:
        # copy canvas boxes to current annotation and mark dirty
        if 0 <= self.current_index < len(self.images):
            img = self.images[self.current_index]
            ann = Annotation()
            for b in self.canvas._boxes:
                ann.add(b)
            self.annotations[img] = ann
            self.dirty[img] = True
        self._refresh_box_list()

    def _mark_dirty(self) -> None:
        if 0 <= self.current_index < len(self.images):
            self.dirty[self.images[self.current_index]] = True

    def _save_current_in_memory(self) -> None:
        # called before navigation to preserve edits without writing to disk
        if 0 <= self.current_index < len(self.images):
            img = self.images[self.current_index]
            ann = Annotation()
            for b in self.canvas._boxes:
                ann.add(b)
            self.annotations[img] = ann
            self.dirty[img] = True

    def _add_saved_image(self, name: str) -> None:
        """Append image name to the saved-list widget and update total count."""
        # ignore duplicates
        existing = [self.saved_list.item(i).text() for i in range(self.saved_list.count())]
        if name not in existing:
            self.saved_list.addItem(name)
            self.saved_count_label.setText(f"Toplam: {self.saved_list.count()}")

    # helper methods for file dialogs are defined later in the file; the earlier
    # duplicates have been removed for clarity.

    def _set_mode(self, mode: CanvasMode) -> None:
        """Switch canvas mode and update button states."""
        self.canvas.set_mode(mode)
        self.navigate_btn.setChecked(mode == CanvasMode.NAVIGATE)
        self.mark_btn.setChecked(mode == CanvasMode.MARK)
        self.select_btn.setChecked(mode == CanvasMode.SELECT)

    def next_image(self) -> None:
        if self.current_index < 0:
            return
        self._save_current_in_memory()
        if self.current_index + 1 < len(self.images):
            self.current_index += 1
            self._load_current()
            # ensure canvas is in navigate mode after moving
            self._set_mode(CanvasMode.NAVIGATE)

    def _choose_images(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if path:
            self._image_dir_edit.setText(path)
            self.saved_list.clear()
            self.saved_count_label.setText("Toplam: 0")
            self.load_images(Path(path))

    def _choose_labels(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Label Folder")
        if path:
            self._label_dir_edit.setText(path)
            # we currently assume labels are stored alongside images
            # future implementation may sync or copy files

    def prev_image(self) -> None:
        if self.current_index < 0:
            return
        self._save_current_in_memory()
        if self.current_index - 1 >= 0:
            self.current_index -= 1
            self._load_current()
            # ensure canvas is in navigate mode after moving
            self._set_mode(CanvasMode.NAVIGATE)

    def load_images(self, folder: Path) -> None:
        self.images = sorted(folder.glob("*.jpg")) + sorted(folder.glob("*.png")) + sorted(
            folder.glob("*.jpeg")
        )
        self.current_index = 0 if self.images else -1
        # enable/adjust goto controls
        if self.images:
            self.goto_spin.setEnabled(True)
            self.goto_spin.setRange(1, len(self.images))
            self.goto_button.setEnabled(True)
        else:
            self.goto_spin.setEnabled(False)
            self.goto_spin.setRange(1, 1)
            self.goto_button.setEnabled(False)
        self._load_current()

    def _load_current(self) -> None:
        if self.current_index < 0 or self.current_index >= len(self.images):
            return
        img_path = self.images[self.current_index]
        # if annotation already in memory, reuse; otherwise read from disk
        if img_path in self.annotations:
            self.annotation = self.annotations[img_path]
        else:
            self._load_annotation_for(img_path)
            self.annotations[img_path] = self.annotation
        self.dirty.setdefault(img_path, False)
        # update canvas
        self.canvas.load_image(img_path)
        self.canvas._boxes = self.annotation.boxes.copy()
        self.canvas._selected_box = None
        self.canvas.new_box_class = self.class_spin.value()
        self.canvas.boxes_changed.emit()
        self.canvas.update()
        self.index_label.setText(f"{self.current_index+1} / {len(self.images)}")
        # update goto control
        try:
            self.goto_spin.setRange(1, len(self.images))
            self.goto_spin.setValue(self.current_index + 1)
            self.goto_spin.setEnabled(True)
            self.goto_button.setEnabled(True)
        except Exception:
            pass
        # automatically switch to navigate mode when a new image is shown
        self._set_mode(CanvasMode.NAVIGATE)

    def go_to_image(self) -> None:
        """Jump directly to the image number entered in the spinbox (1-based)."""
        if self.current_index < 0:
            return
        idx = self.goto_spin.value() - 1
        if 0 <= idx < len(self.images):
            self._save_current_in_memory()
            self.current_index = idx
            self._load_current()

    def delete_current_image(self) -> None:
        """Delete the current image file and its label after confirmation."""
        if self.current_index < 0 or self.current_index >= len(self.images):
            return
        img_path = self.images[self.current_index]
        reply = QtWidgets.QMessageBox.question(
            self,
            "Silme Onayı",
            f"'{img_path.name}' dosyasını ve etiketi silmek istediğinize emin misiniz?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
        )
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        # attempt to remove image file
        try:
            if img_path.exists():
                img_path.unlink()
        except Exception:
            self._show_temporary_message("Fotoğraf silinemedi")

        # remove corresponding label
        label_dir_text = self._label_dir_edit.text().strip()
        if label_dir_text:
            label_path = Path(label_dir_text) / img_path.with_suffix(".txt").name
        else:
            label_path = img_path.with_suffix(".txt")
        try:
            if label_path.exists():
                label_path.unlink()
        except Exception:
            pass

        # remove from saved list if present
        for i in range(self.saved_list.count()):
            if self.saved_list.item(i).text() == img_path.name:
                self.saved_list.takeItem(i)
                break
        self.saved_count_label.setText(f"Toplam: {self.saved_list.count()}")

        # remove from internal state
        self.annotations.pop(img_path, None)
        self.dirty.pop(img_path, None)
        del self.images[self.current_index]

        # update navigation
        if not self.images:
            self.current_index = -1
            self.canvas._pixmap = None
            self.canvas._boxes = []
            self.canvas._selected_box = None
            self.canvas.update()
            self.index_label.setText("0 / 0")
            self.goto_spin.setEnabled(False)
            self.goto_spin.setRange(1, 1)
            self.goto_button.setEnabled(False)
            self._show_temporary_message("Fotoğraf silindi")
            return

        if self.current_index >= len(self.images):
            self.current_index = len(self.images) - 1
        self._load_current()
        self._show_temporary_message("Fotoğraf silindi")

    def _load_annotation_for(self, img_path: Path) -> None:
        # determine label path (use separate label folder if provided)
        label_dir_text = self._label_dir_edit.text().strip()
        if label_dir_text:
            label_path = Path(label_dir_text) / img_path.with_suffix(".txt").name
        else:
            label_path = img_path.with_suffix(".txt")
        self.annotation = Annotation()
        if label_path.exists():
            from PIL import Image

            with Image.open(img_path) as im:
                width, height = im.size
            entries = read_yolo_labels(label_path)
            for class_id, xc, yc, w, h in entries:
                # convert normalized to image coordinates
                x_center = xc * width
                y_center = yc * height
                box_w = w * width
                box_h = h * height
                x1 = x_center - box_w / 2
                y1 = y_center - box_h / 2
                self.annotation.add(BoundingBox(class_id, x1, y1, x1 + box_w, y1 + box_h))
            self.canvas._boxes = self.annotation.boxes.copy()
            self.canvas.update()

    def save_current_annotation(self) -> None:
        if self.current_index < 0 or self.current_index >= len(self.images):
            return
        img_path = self.images[self.current_index]
        # Determine output label path (separate folder or same dir)
        label_dir_text = self._label_dir_edit.text().strip()
        if label_dir_text:
            label_path = Path(label_dir_text) / img_path.with_suffix(".txt").name
        else:
            label_path = img_path.with_suffix(".txt")
        entries = []
        from PIL import Image

        with Image.open(img_path) as im:
            width, height = im.size
        for box in self.canvas._boxes:
            x_center = (box.x1 + box.x2) / 2 / width
            y_center = (box.y1 + box.y2) / 2 / height
            w_norm = (box.x2 - box.x1) / width
            h_norm = (box.y2 - box.y1) / height
            entries.append((box.class_id, x_center, y_center, w_norm, h_norm))
        write_yolo_labels(label_path, entries)
        # show a small non-intrusive notification instead of a dialog
        self._show_temporary_message("Kaydedildi")
        # add to saved-list UI
        self._add_saved_image(img_path.name)
        # mark this image clean
        self.dirty[self.images[self.current_index]] = False
