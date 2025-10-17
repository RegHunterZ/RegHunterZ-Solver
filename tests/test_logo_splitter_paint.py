
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter
app = QApplication.instance() or QApplication(sys.argv)
from ai_coach.ui.main_window import MainWindow, LogoSplitter

def test_logo_splitter_paints():
    w = MainWindow()
    sp = w.centralWidget()
    assert isinstance(sp, LogoSplitter)
    img = QImage(1200, 800, QImage.Format.Format_ARGB32)
    p = QPainter(img); sp.render(p); p.end()  # should not crash
