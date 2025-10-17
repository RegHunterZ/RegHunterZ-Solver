
# Single-window launcher delegating to app.main (robust for script or package run)
import os, sys
# Ensure parent dir (which contains 'app') is on sys.path when running as script
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# HiDPI rounding policy before creating QApplication
os.environ.setdefault("QT_HIGH_DPI_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QGuiApplication
try:
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(QGuiApplication.HighDpiScaleFactorRoundingPolicy.PassThrough)
except Exception:
    pass

from app.main import MainWindow  # now resolvable both ways

if __name__ == "__main__":
    print("[BOOT] AI Coach (CostSaver) starting...")
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
