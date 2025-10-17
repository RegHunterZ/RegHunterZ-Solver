
import sys
from PyQt6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)
from ai_coach.ui.main_window import MainWindow

def test_diag_button_exists():
    w = MainWindow()
    btn = getattr(w, '_diag_btn', None)
    assert btn is not None and btn.text() == "Diag"
