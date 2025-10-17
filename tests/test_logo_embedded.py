
import sys
from PyQt6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)
from ai_coach.ui.main_window import MainWindow

def test_embedded_logo_loads():
    w = MainWindow()
    assert not w._load_logo_pix().isNull()
