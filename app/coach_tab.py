from ai_coach.ui.visual_replayer import VisualReplayer

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QSplitter, QVBoxLayout, QLabel
from ai_coach.ui.replayer_widget import ReplayerWidget
from ai_coach.ui.chat_widget import ChatWidget

QSS = '''
QWidget {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #0f1e2e, stop:1 #2f3b47);
    color: #ffffff;
    font-size: 12px;
}
QTextEdit, QTableWidget, QLineEdit, QComboBox {
    background-color: rgba(20, 30, 40, 0.9);
    color: #ffffff;
}
QPushButton {
    background-color: #2a6ae8; color: white; border-radius: 6px; padding: 6px 10px;
}
QGroupBox { border: 1px solid rgba(255,255,255,0.12); margin-top: 12px; padding-top: 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
'''
class CoachTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(QSS)
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.replayer = ReplayerWidget()
        self.chat = ChatWidget()
        splitter.addWidget(self.replayer); splitter.addWidget(self.chat)
        splitter.setStretchFactor(0,3); splitter.setStretchFactor(1,2)
        try:
            splitter.setSizes([1100, 420])
        except Exception:
            pass
        lay.addWidget(splitter)
        self.replayer.onParsed.connect(self.chat.onParsedHand)

# create visual replayer on the right big panel if layout available
try:
    self.visual_replayer = VisualReplayer(self)
    self.right_container.addWidget(self.visual_replayer)
except Exception:
    pass
