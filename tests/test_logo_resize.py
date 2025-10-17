
import sys
from PyQt6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)
from ai_coach.ui.main_window import MainWindow

def test_logo_resizes_and_centers():
    w = MainWindow()
    w.resize(1400,900); w._place_logo(); s1 = (w._logo_label.width(), w._logo_label.height())
    w.resize(900,600);  w._place_logo(); s2 = (w._logo_label.width(), w._logo_label.height())
    assert s2[0] < s1[0] and s2[1] < s1[1]
