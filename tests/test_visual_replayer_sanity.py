
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter
app = QApplication.instance() or QApplication(sys.argv)
from ai_coach.ui.visual_replayer import VisualReplayer

def test_no_crash_on_empty_actions():
    w = VisualReplayer()
    img = QImage(1000,700, QImage.Format.Format_ARGB32)
    p = QPainter(img); w.render(p); p.end()

def test_draw_with_action():
    w = VisualReplayer()
    w.players = {k: {'stack':100.0} for k in ["UTG","HJ","CO","BTN","SB","BB"]}
    w.actions = [{'pos':'BTN','move':'opens','size':2.5}]
    w.step = 0
    img = QImage(1200,800, QImage.Format.Format_ARGB32)
    p = QPainter(img); w.render(p); p.end()
