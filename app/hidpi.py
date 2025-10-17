from PyQt6.QtGui import QGuiApplication
from PyQt6.QtCore import Qt

def ensure_policy_before_qapp():
    # Only set policy if no instance exists yet
    if QGuiApplication.instance() is None:
        try:
            QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )
        except Exception:
            pass
