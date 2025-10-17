
import sys
from PyQt6.QtWidgets import QApplication, QLabel
app = QApplication.instance() or QApplication(sys.argv)
from ai_coach.ui.main_window import MainWindow

def test_purge_removes_legacy_labels():
    w = MainWindow()
    lbl = QLabel("RegHunterZ", w); lbl.setObjectName("BackgroundLogo"); lbl.show()
    w._purge_legacy_overlays()
    # after purge, label should be hidden and unparented or not visible
    assert not lbl.isVisible() or lbl.parent() is None
