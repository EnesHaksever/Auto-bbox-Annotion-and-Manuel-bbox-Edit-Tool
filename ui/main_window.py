"""Main application window containing mode selection and central widgets."""

from __future__ import annotations

from PyQt6 import QtWidgets, QtGui


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Object Detection Dataset Tool")
        
        # central widget will change depending on mode
        self._central_widget = QtWidgets.QStackedWidget()
        self.setCentralWidget(self._central_widget)

        # mode toolbar
        toolbar = self.addToolBar("Modes")
        self.auto_action = QtGui.QAction("Auto Label", self)
        self.auto_action.setCheckable(True)
        self.edit_action = QtGui.QAction("Edit Mode", self)
        self.edit_action.setCheckable(True)
        self.shortcut_action = QtGui.QAction("Edit Shortcuts", self)
        self.shortcut_action.setCheckable(True)
        toolbar.addAction(self.auto_action)
        toolbar.addAction(self.edit_action)
        toolbar.addAction(self.shortcut_action)

        # placeholders for modes
        # to be set by controller logic

    def set_mode_widget(self, widget: QtWidgets.QWidget) -> None:
        """Switch the central widget to the given mode widget."""
        index = self._central_widget.indexOf(widget)
        if index == -1:
            self._central_widget.addWidget(widget)
            index = self._central_widget.indexOf(widget)
        self._central_widget.setCurrentIndex(index)
        class_name = widget.__class__.__name__
        self.auto_action.setChecked(class_name == "AutoLabelMode")
        self.edit_action.setChecked(class_name == "EditMode")
        self.shortcut_action.setChecked(class_name == "EditShortcutsMode")
