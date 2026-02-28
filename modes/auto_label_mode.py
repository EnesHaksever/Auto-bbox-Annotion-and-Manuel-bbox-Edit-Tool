"""Implementation of the auto labeling workflow and UI interactions."""

from __future__ import annotations

from pathlib import Path
from typing import List

from PyQt6 import QtCore, QtGui, QtWidgets

from core.detection_engine import DetectionEngine, DetectionResult
from core.yolo_label_parser import write_yolo_labels


class AutoLabelMode(QtWidgets.QWidget):
    """Widget encapsulating the auto-label functionality."""

    progress_updated = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # UI elements
        self._layout = QtWidgets.QVBoxLayout(self)

        self._images_dir_edit = QtWidgets.QLineEdit()
        self._images_dir_button = QtWidgets.QPushButton("Browse...")
        h = QtWidgets.QHBoxLayout()
        h.addWidget(self._images_dir_edit)
        h.addWidget(self._images_dir_button)
        self._layout.addWidget(QtWidgets.QLabel("Images folder:"))
        self._layout.addLayout(h)

        self._weights_edit = QtWidgets.QLineEdit()
        self._weights_button = QtWidgets.QPushButton("Browse...")
        h2 = QtWidgets.QHBoxLayout()
        h2.addWidget(self._weights_edit)
        h2.addWidget(self._weights_button)
        self._layout.addWidget(QtWidgets.QLabel("Model weights (.pt):"))
        self._layout.addLayout(h2)

        self._output_dir_edit = QtWidgets.QLineEdit()
        self._output_dir_button = QtWidgets.QPushButton("Browse...")
        h3 = QtWidgets.QHBoxLayout()
        h3.addWidget(self._output_dir_edit)
        h3.addWidget(self._output_dir_button)
        self._layout.addWidget(QtWidgets.QLabel("Output labels folder:"))
        self._layout.addLayout(h3)

        self._confidence_spin = QtWidgets.QDoubleSpinBox()
        self._confidence_spin.setRange(0.0, 1.0)
        self._confidence_spin.setSingleStep(0.05)
        self._confidence_spin.setValue(0.25)
        self._layout.addWidget(QtWidgets.QLabel("Confidence threshold:"))
        self._layout.addWidget(self._confidence_spin)

        self._start_button = QtWidgets.QPushButton("Run Auto Label")
        self._layout.addWidget(self._start_button)
        self._progress = QtWidgets.QProgressBar()
        self._layout.addWidget(self._progress)

        # connections (methods defined later)
        self._images_dir_button.clicked.connect(self._choose_images_dir)
        self._weights_button.clicked.connect(self._choose_weights_file)
        self._output_dir_button.clicked.connect(self._choose_output_dir)
        self._start_button.clicked.connect(self._on_start_clicked)

        # internal state
        self.engine: DetectionEngine | None = None
        self._thread: QtCore.QThread | None = None

        # keep track of widgets we should disable while worker runs
        self._run_controls = [
            self._images_dir_edit,
            self._images_dir_button,
            self._weights_edit,
            self._weights_button,
            self._output_dir_edit,
            self._output_dir_button,
            self._confidence_spin,
            self._start_button,
        ]

    # directory chooser callbacks
    def _choose_images_dir(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Images Folder")
        if path:
            self._images_dir_edit.setText(path)

    def _choose_weights_file(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Weights File", filter="Weights (*.pt)")
        if path:
            self._weights_edit.setText(path)

    def _choose_output_dir(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if path:
            self._output_dir_edit.setText(path)

    def _set_controls_enabled(self, enabled: bool) -> None:
        """Enable/disable all input widgets during processing."""
        for w in self._run_controls:
            w.setEnabled(enabled)

    def _on_start_clicked(self) -> None:
        # gather inputs from user widgets and start worker thread
        images_dir = Path(self._images_dir_edit.text())
        weights = Path(self._weights_edit.text())
        output_dir = Path(self._output_dir_edit.text())
        conf = float(self._confidence_spin.value())

        if not images_dir.is_dir():
            QtWidgets.QMessageBox.warning(self, "Invalid folder", "Images folder does not exist.")
            return
        if not weights.is_file():
            QtWidgets.QMessageBox.warning(self, "Invalid file", "Weights file does not exist.")
            return
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            # check for existing .txt labels
            existing = list(output_dir.glob("*.txt"))
            if existing:
                resp = QtWidgets.QMessageBox.question(
                    self,
                    "Overwrite existing labels?",
                    "The output folder already contains label files. Overwrite all?",
                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                )
                if resp != QtWidgets.QMessageBox.StandardButton.Yes:
                    return

        # prepare UI state
        self._progress.setValue(0)
        self._set_controls_enabled(False)
        print("[AutoLabelMode] starting worker thread")

        # create worker thread and keep references so they are not GC'd
        self._worker = _AutoLabelWorker(images_dir, output_dir, weights, conf)
        self._thread = QtCore.QThread()
        self._worker.moveToThread(self._thread)

        # wire signals before starting the thread so we catch early errors
        self._worker.progress_updated.connect(self.progress_updated)
        self._worker.finished.connect(self.finished)
        self._worker.error.connect(self.error)
        self.progress_updated.connect(self._progress.setValue)
        self.finished.connect(self._on_finished)
        self.error.connect(self._on_error)

        self._thread.started.connect(self._worker.run)
        # cleanup when thread ends
        self._thread.finished.connect(self._on_thread_finished)
        self._thread.start()
        print("[AutoLabelMode] thread started")

    def _on_finished(self) -> None:
        print("[AutoLabelMode] received finished signal")
        QtWidgets.QMessageBox.information(self, "Done", "Auto labeling finished.")
        self._set_controls_enabled(True)
        if self._thread:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
        self._worker = None

    def _on_error(self, msg: str) -> None:
        print(f"[AutoLabelMode] received error signal: {msg}")
        QtWidgets.QMessageBox.critical(self, "Error", msg)
        self._set_controls_enabled(True)
        if self._thread:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
        self._worker = None

    def _on_error(self, msg: str) -> None:
        QtWidgets.QMessageBox.critical(self, "Error", msg)
        self._set_controls_enabled(True)
        if self._thread:
            self._thread.quit()
            self._thread.wait()
            self._thread = None

    def _on_thread_finished(self) -> None:
        print("[AutoLabelMode] thread finished cleanup")
        # called when QThread emits finished; ensure references are cleared
        if self._thread:
            self._thread.deleteLater()
            self._thread = None


    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        # ensure worker thread is stopped before widget is destroyed
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)
        super().closeEvent(event)


class _AutoLabelWorker(QtCore.QObject):
    progress_updated = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)

    def __init__(
        self,
        image_dir: Path,
        output_dir: Path,
        weights: Path,
        confidence: float,
    ):
        super().__init__()
        self.image_dir = image_dir
        self.output_dir = output_dir
        self.weights = weights
        self.confidence = confidence

    def run(self) -> None:
        try:
            # Collect images first
            images = (
                sorted(self.image_dir.glob("*.jpg"))
                + sorted(self.image_dir.glob("*.png"))
                + sorted(self.image_dir.glob("*.jpeg"))
            )
            
            total = len(images)
            if total == 0:
                self.error.emit("No images found in the selected folder.")
                return

            # Emit 0% as we start loading model
            self.progress_updated.emit(0)

            # Load model (this may take time)
            engine = DetectionEngine(self.weights, self.confidence)
            engine.load_model()

            # Emit 5% once model is loaded
            self.progress_updated.emit(5)

            from PIL import Image

            # Process each image
            for i, img_path in enumerate(images, start=1):
                try:
                    # Run inference
                    results = list(engine.infer_image(img_path))
                    entries: List[tuple] = []

                    # Get image dimensions for normalization
                    with Image.open(img_path) as im:
                        width, height = im.size

                    # Convert detections to YOLO format
                    for r in results:
                        class_id, x_center, y_center, w_norm, h_norm = r.to_yolo_format((width, height))
                        entries.append((class_id, x_center, y_center, w_norm, h_norm))

                    # Write label file
                    label_file = self.output_dir / img_path.with_suffix(".txt").name
                    write_yolo_labels(label_file, entries)

                except Exception as img_error:
                    # Log but continue with next image
                    import logging
                    logging.warning(f"Failed to process {img_path}: {img_error}")
                    continue

                # Update progress (5% to 100%)
                progress_pct = 5 + int((i / total) * 95)
                self.progress_updated.emit(progress_pct)

            self.progress_updated.emit(100)
            self.finished.emit()

        except Exception as e:
            import traceback
            self.error.emit(f"Auto-labeling failed: {str(e)}\n{traceback.format_exc()}")

