"""Widget for configuring Edit Mode keyboard shortcuts."""

from __future__ import annotations

from PyQt6 import QtGui, QtWidgets

from modes.edit_mode import EditMode


class EditShortcutsMode(QtWidgets.QWidget):
    """Dedicated page for editing Edit Mode shortcuts."""

    def __init__(self, edit_mode: EditMode, parent=None):
        super().__init__(parent)
        self._edit_mode = edit_mode
        self._edits: dict[str, QtWidgets.QKeySequenceEdit] = {}

        layout = QtWidgets.QVBoxLayout(self)
        title = QtWidgets.QLabel("Edit Mode Shortcut Ayarları")
        title.setStyleSheet("font-weight: 600; font-size: 14px;")
        layout.addWidget(title)

        help_text = QtWidgets.QLabel(
            "Buradaki atamalar Edit Mode ekranında geçerlidir."
        )
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        form = QtWidgets.QFormLayout()
        for action_key in self._edit_mode.shortcut_action_keys():
            edit = QtWidgets.QKeySequenceEdit(
                self._edit_mode.get_shortcut_sequence(action_key)
            )
            edit.keySequenceChanged.connect(
                lambda seq, key=action_key: self._edit_mode.set_shortcut_sequence(key, seq)
            )
            self._edits[action_key] = edit
            form.addRow(self._edit_mode.get_shortcut_label(action_key), edit)
        layout.addLayout(form)

        reset_btn = QtWidgets.QPushButton("Varsayılanlara Dön")
        reset_btn.clicked.connect(self._reset_defaults)
        layout.addWidget(reset_btn)
        layout.addStretch()

    def _reset_defaults(self) -> None:
        for action_key, edit in self._edits.items():
            seq = self._edit_mode.get_default_shortcut_sequence(action_key)
            edit.setKeySequence(seq)
            self._edit_mode.set_shortcut_sequence(action_key, seq)
