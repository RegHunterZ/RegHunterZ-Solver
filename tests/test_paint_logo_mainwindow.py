
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter
app = QApplication.instance() or QApplication(sys.argv)
from ai_coach.ui.main_window import MainWindow

def test_mainwindow_paint_logo():
    w = MainWindow()
    img = QImage(1200, 800, QImage.Format.Format_ARGB32)
    p = QPainter(img); w.render(p); p.end()  # should not crash
