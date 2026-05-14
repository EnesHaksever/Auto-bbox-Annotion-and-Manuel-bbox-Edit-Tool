"""Widget for copying a contiguous range of images and labels."""

from __future__ import annotations

from pathlib import Path
import shutil
from typing import List

from PyQt6 import QtCore, QtWidgets


class CopyRangeMode(QtWidgets.QWidget):
    progress_updated = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(str, str)
    error = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QtWidgets.QVBoxLayout(self)

        self._images_dir_edit = QtWidgets.QLineEdit()
        self._images_dir_button = QtWidgets.QPushButton("Browse...")
        images_row = QtWidgets.QHBoxLayout()
        images_row.addWidget(self._images_dir_edit)
        images_row.addWidget(self._images_dir_button)
        self._layout.addWidget(QtWidgets.QLabel("Images folder:"))
        self._layout.addLayout(images_row)

        self._labels_dir_edit = QtWidgets.QLineEdit()
        self._labels_dir_button = QtWidgets.QPushButton("Browse...")
        labels_row = QtWidgets.QHBoxLayout()
        labels_row.addWidget(self._labels_dir_edit)
        labels_row.addWidget(self._labels_dir_button)
        self._layout.addWidget(QtWidgets.QLabel("Labels folder:"))
        self._layout.addLayout(labels_row)

        self._output_images_edit = QtWidgets.QLineEdit()
        self._output_images_button = QtWidgets.QPushButton("Browse...")
        output_images_row = QtWidgets.QHBoxLayout()
        output_images_row.addWidget(self._output_images_edit)
        output_images_row.addWidget(self._output_images_button)
        self._layout.addWidget(QtWidgets.QLabel("Output images folder:"))
        self._layout.addLayout(output_images_row)

        self._output_labels_edit = QtWidgets.QLineEdit()
        self._output_labels_button = QtWidgets.QPushButton("Browse...")
        output_labels_row = QtWidgets.QHBoxLayout()
        output_labels_row.addWidget(self._output_labels_edit)
        output_labels_row.addWidget(self._output_labels_button)
        self._layout.addWidget(QtWidgets.QLabel("Output labels folder:"))
        self._layout.addLayout(output_labels_row)

        range_layout = QtWidgets.QHBoxLayout()
        self._start_spin = QtWidgets.QSpinBox()
        self._start_spin.setMinimum(1)
        self._start_spin.setMaximum(9999999)
        self._start_spin.setValue(1)
        self._end_spin = QtWidgets.QSpinBox()
        self._end_spin.setMinimum(1)
        self._end_spin.setMaximum(9999999)
        self._end_spin.setValue(1)
        range_layout.addWidget(QtWidgets.QLabel("Start index:"))
        range_layout.addWidget(self._start_spin)
        range_layout.addSpacing(20)
        range_layout.addWidget(QtWidgets.QLabel("End index:"))
        range_layout.addWidget(self._end_spin)
        self._layout.addWidget(QtWidgets.QLabel("Copy range (1-based image index):"))
        self._layout.addLayout(range_layout)

        self._start_button = QtWidgets.QPushButton("Copy Range")
        self._layout.addWidget(self._start_button)

        self._progress = QtWidgets.QProgressBar()
        self._layout.addWidget(self._progress)

        self._result_label = QtWidgets.QLabel("")
        self._result_label.setWordWrap(True)
        self._layout.addWidget(self._result_label)

        self._images_dir_button.clicked.connect(self._choose_images_dir)
        self._labels_dir_button.clicked.connect(self._choose_labels_dir)
        self._output_images_button.clicked.connect(self._choose_output_images_dir)
        self._output_labels_button.clicked.connect(self._choose_output_labels_dir)
        self._start_button.clicked.connect(self._on_start_clicked)

        self._run_controls = [
            self._images_dir_edit,
            self._images_dir_button,
            self._labels_dir_edit,
            self._labels_dir_button,
            self._output_images_edit,
            self._output_images_button,
            self._output_labels_edit,
            self._output_labels_button,
            self._start_spin,
            self._end_spin,
            self._start_button,
        ]

        self._worker: _CopyRangeWorker | None = None
        self._thread: QtCore.QThread | None = None

        self.progress_updated.connect(self._progress.setValue)
        self.finished.connect(self._on_finished)
        self.error.connect(self._on_error)

    def _choose_images_dir(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Images Folder")
        if path:
            self._images_dir_edit.setText(path)

    def _choose_labels_dir(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Labels Folder")
        if path:
            self._labels_dir_edit.setText(path)

    def _choose_output_images_dir(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Images Folder")
        if path:
            self._output_images_edit.setText(path)

    def _choose_output_labels_dir(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Labels Folder")
        if path:
            self._output_labels_edit.setText(path)

    def _set_controls_enabled(self, enabled: bool) -> None:
        for w in self._run_controls:
            w.setEnabled(enabled)

    def _on_start_clicked(self) -> None:
        images_dir = Path(self._images_dir_edit.text())
        labels_dir = Path(self._labels_dir_edit.text())
        output_images_dir = Path(self._output_images_edit.text())
        output_labels_dir = Path(self._output_labels_edit.text())
        start_idx = int(self._start_spin.value())
        end_idx = int(self._end_spin.value())

        if not images_dir.is_dir():
            QtWidgets.QMessageBox.warning(self, "Invalid folder", "Images folder does not exist.")
            return
        if not labels_dir.is_dir():
            QtWidgets.QMessageBox.warning(self, "Invalid folder", "Labels folder does not exist.")
            return
        if not self._output_images_edit.text():
            QtWidgets.QMessageBox.warning(self, "Invalid folder", "Please select an output images folder.")
            return
        if not self._output_labels_edit.text():
            QtWidgets.QMessageBox.warning(self, "Invalid folder", "Please select an output labels folder.")
            return
        if not output_images_dir.exists():
            try:
                output_images_dir.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                QtWidgets.QMessageBox.warning(self, "Invalid folder", f"Cannot create output images folder: {exc}")
                return
        if not output_labels_dir.exists():
            try:
                output_labels_dir.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                QtWidgets.QMessageBox.warning(self, "Invalid folder", f"Cannot create output labels folder: {exc}")
                return
        if end_idx < start_idx:
            QtWidgets.QMessageBox.warning(self, "Invalid range", "End index must be greater than or equal to start index.")
            return

        self._progress.setValue(0)
        self._result_label.setText("")
        self._set_controls_enabled(False)

        self._worker = _CopyRangeWorker(
            images_dir,
            labels_dir,
            output_images_dir,
            output_labels_dir,
            start_idx,
            end_idx,
        )
        self._thread = QtCore.QThread()
        self._worker.moveToThread(self._thread)

        self._worker.progress_updated.connect(self.progress_updated)
        self._worker.finished.connect(self.finished)
        self._worker.error.connect(self.error)
        self._thread.started.connect(self._worker.run)
        self._thread.finished.connect(self._on_thread_finished)
        self._thread.start()

    def _on_finished(self, images_path: str, labels_path: str) -> None:
        self._set_controls_enabled(True)
        self._thread and self._thread.quit()
        self._thread and self._thread.wait()
        self._thread = None
        self._worker = None
        self._result_label.setText(
            f"Copied images to: {images_path}\nCopied labels to: {labels_path}"
        )

    def _on_error(self, msg: str) -> None:
        QtWidgets.QMessageBox.critical(self, "Error", msg)
        self._set_controls_enabled(True)
        if self._thread:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
        self._worker = None

    def _on_thread_finished(self) -> None:
        if self._thread:
            self._thread.deleteLater()
            self._thread = None


class _CopyRangeWorker(QtCore.QObject):
    progress_updated = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(str, str)
    error = QtCore.pyqtSignal(str)

    def __init__(
        self,
        images_dir: Path,
        labels_dir: Path,
        output_images_dir: Path,
        output_labels_dir: Path,
        start_idx: int,
        end_idx: int,
    ):
        super().__init__()
        self.images_dir = images_dir
        self.labels_dir = labels_dir
        self.output_images_dir = output_images_dir
        self.output_labels_dir = output_labels_dir
        self.start_idx = start_idx
        self.end_idx = end_idx

    def _collect_sorted_images(self) -> List[Path]:
        images: List[Path] = []
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tif", "*.tiff"]:
            images.extend(self.images_dir.glob(ext))
        return sorted(images, key=lambda p: p.name.lower())

    def run(self) -> None:
        try:
            images = self._collect_sorted_images()
            total = len(images)
            if total == 0:
                self.error.emit("No images found in the selected images folder.")
                return
            if self.start_idx < 1 or self.end_idx > total:
                self.error.emit(
                    f"Range must be between 1 and {total}."
                )
                return

            selection = images[self.start_idx - 1 : self.end_idx]
            selected_count = len(selection)
            if selected_count == 0:
                self.error.emit("No images found in the specified range.")
                return

            for i, image_path in enumerate(selection, start=1):
                target_image_path = self.output_images_dir / image_path.name
                shutil.copy2(image_path, target_image_path)

                label_path = self.labels_dir / image_path.with_suffix(".txt").name
                if label_path.exists():
                    target_label_path = self.output_labels_dir / label_path.name
                    shutil.copy2(label_path, target_label_path)

                progress = int((i / selected_count) * 100)
                self.progress_updated.emit(progress)

            self.progress_updated.emit(100)
            self.finished.emit(str(self.output_images_dir), str(self.output_labels_dir))
        except Exception as exc:
            self.error.emit(f"Copy range failed: {exc}")
