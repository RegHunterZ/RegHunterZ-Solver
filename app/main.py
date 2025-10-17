
from .hidpi import ensure_policy_before_qapp
ensure_policy_before_qapp()

import sys, os
from PyQt6 import QtWidgets, QtGui, QtCore

from .coach_tab import CoachTab


class FullLogoWidget(QtWidgets.QLabel):
    """Full-window logo that scales to fill while preserving aspect ratio (cover)."""
    def __init__(self, candidate_paths, parent=None):
        super().__init__(parent)
        self.setObjectName("FullLogoWidget")
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.setMinimumSize(10, 10)
        self._pixmap = None
        for p in candidate_paths:
            if os.path.exists(p):
                pm = QtGui.QPixmap(p)
                if not pm.isNull():
                    self._pixmap = pm
                    break
        self._update_scaled()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._update_scaled()

    def _update_scaled(self):
        if not self._pixmap:
            self.clear(); return
        if self.width() <= 0 or self.height() <= 0:
            return
        # Cover behavior: expand to fill and crop overflow
        scaled = self._pixmap.scaled(self.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
        self.setPixmap(scaled)


QSS = '''
QWidget { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0f1e2e, stop:1 #2f3b47); color:#fff; font-size:12px; }
QTabWidget::pane { border: 0; }
QTabBar::tab { background: rgba(255,255,255,0.06); padding: 8px 14px; margin: 2px; border-radius: 6px; }
QTabBar::tab:selected { background: #2a6ae8; color: #fff; }
'''

class LogoWidget(QtWidgets.QLabel):
    def __init__(self, img_candidates, parent=None):
        super().__init__(parent)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(200, 120)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self._pix = None
        for path in img_candidates:
            if path and os.path.exists(path):
                self._pix = QtGui.QPixmap(path)
                break
        if self._pix is None:
            self.setText("RegHunterZ")
        else:
            self.setText("")
    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if self._pix:
            size = self.size()
            scaled = self._pix.scaled(size, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
            self.setPixmap(scaled)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RegHunterZ — KKPoker AI Replayer + Coach")
        self.resize(1500, 950)
        self.setStyleSheet(QSS)

        tabs = QtWidgets.QTabWidget(self)
        self.setCentralWidget(tabs)

        here = os.path.dirname(__file__)
        candidates = [
            os.path.join(here, "..", "reghuterz-hatternelkul_1.png"),
            os.path.join(here, "reghuterz-hatternelkul_1.png"),
            os.path.join(os.getcwd(), "reghuterz-hatternelkul_1.png"),
            os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "reghuterz-hatternelkul_1.png"),
        ]
        candidates = [os.path.abspath(p) for p in candidates]

        home = QtWidgets.QWidget(); lay = QtWidgets.QVBoxLayout(home)
        lay.setContentsMargins(0,0,0,0)
        logo = FullLogoWidget(candidates, home)
        lay.setContentsMargins(0,0,0,0)
        logo.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        lay.addWidget(logo)
        tabs.addTab(home, "RegHunterZ")

        coach = CoachTab(self)
        tabs.addTab(coach, "Edző")

def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow(); w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
