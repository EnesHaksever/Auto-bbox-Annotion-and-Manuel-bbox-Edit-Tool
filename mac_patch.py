"""
mac_patch.py  —  macOS 15 uyumlu başlatıcı
Emoji → ASCII dönüşümü ile CoreText SIGBUS crash'i önler.
"""

from __future__ import annotations
import os, sys, re

os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
os.environ["QT_MAC_WANTS_LAYER"] = "1"

# ── Emoji temizleyici ──────────────────────────────────────────────────────
EMOJI_RE = re.compile(
    "["
    "\U00010000-\U0010ffff"
    "\U0001F300-\U0001F9FF"
    "\U00002702-\U000027B0"
    "\U0000FE00-\U0000FE0F"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "]+",
    flags=re.UNICODE,
)

def strip_emoji(text: str) -> str:
    return EMOJI_RE.sub("", text).strip()

# ── PyQt6 widget'larını yakala ─────────────────────────────────────────────
from PyQt6 import QtWidgets, QtCore, QtGui

_orig_tb_setText     = QtWidgets.QToolButton.setText
_orig_pb_setText     = QtWidgets.QPushButton.setText
_orig_lb_setText     = QtWidgets.QLabel.setText
_orig_action_setText = QtGui.QAction.setText

def _tb_setText(self, text):     _orig_tb_setText(self, strip_emoji(text))
def _pb_setText(self, text):     _orig_pb_setText(self, strip_emoji(text))
def _lb_setText(self, text):     _orig_lb_setText(self, strip_emoji(text))
def _action_setText(self, text): _orig_action_setText(self, strip_emoji(text))

QtWidgets.QToolButton.setText = _tb_setText
QtWidgets.QPushButton.setText = _pb_setText
QtWidgets.QLabel.setText      = _lb_setText
QtGui.QAction.setText         = _action_setText

# QAction __init__ da yakala (bazı butonlar constructor'da text alır)
_orig_QAction_init = QtGui.QAction.__init__
def _patched_QAction_init(self, *args, **kwargs):
    clean = [strip_emoji(a) if isinstance(a, str) else a for a in args]
    _orig_QAction_init(self, *clean, **kwargs)
QtGui.QAction.__init__ = _patched_QAction_init

# ── PyTorch device ─────────────────────────────────────────────────────────
def get_device():
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            print("Apple MPS (Metal) kullaniliyor.")
            return "mps"
    except ImportError:
        pass
    print("CPU modu kullaniliyor.")
    return "cpu"

DEVICE = get_device()

# ── Ana uygulama ───────────────────────────────────────────────────────────
def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Auto-bbox Annotation Tool")

    # Emoji icermeyen guvenli font
    font = QtGui.QFont("Helvetica Neue", 13)
    font.setStyleHint(QtGui.QFont.StyleHint.SansSerif)
    app.setFont(font)

    from ui.main_window import MainWindow
    from modes.auto_label_mode import AutoLabelMode
    from modes.edit_mode import EditMode

    try:
        from modes.edit_shortcuts_mode import EditShortcutsMode
        from modes.copy_range_mode import CopyRangeMode
        has_extra = True
    except ImportError:
        has_extra = False

    window = MainWindow()
    auto_widget = AutoLabelMode()
    edit_widget = EditMode()

    window.auto_action.triggered.connect(lambda: window.set_mode_widget(auto_widget))
    window.edit_action.triggered.connect(lambda: window.set_mode_widget(edit_widget))

    if has_extra:
        shortcuts_widget  = EditShortcutsMode(edit_widget)
        copy_range_widget = CopyRangeMode()
        window.shortcut_action.triggered.connect(
            lambda: window.set_mode_widget(shortcuts_widget))
        window.copy_range_action.triggered.connect(
            lambda: window.set_mode_widget(copy_range_widget))

    window.set_mode_widget(auto_widget)
    window.show()
    print(f"Uygulama basladi — device={DEVICE}")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
