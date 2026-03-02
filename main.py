"""Entry point for the dataset labeling tool."""

from __future__ import annotations

import sys

from PyQt6 import QtWidgets

from ui.main_window import MainWindow
from modes.auto_label_mode import AutoLabelMode
from modes.edit_mode import EditMode
from modes.edit_shortcuts_mode import EditShortcutsMode


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()

    # create mode widgets
    auto_widget = AutoLabelMode()
    edit_widget = EditMode()
    shortcuts_widget = EditShortcutsMode(edit_widget)

    # wire toolbar actions
    window.auto_action.triggered.connect(lambda: window.set_mode_widget(auto_widget))
    window.edit_action.triggered.connect(lambda: window.set_mode_widget(edit_widget))
    window.shortcut_action.triggered.connect(lambda: window.set_mode_widget(shortcuts_widget))

    # default to auto
    window.set_mode_widget(auto_widget)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
