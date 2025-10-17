
from PyQt6.QtWidgets import QDialog, QGridLayout, QPushButton, QSizePolicy
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap

# Card constants
RANKS = ['A','K','Q','J','T','9','8','7','6','5','4','3','2']
SUITS = ['h','d','c','s']

# Asset folder
import os
ASSETS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "cards_kk")

def _icon_for(rank, suit):
    p = os.path.join(ASSETS, f"{rank}{suit}.png")
    return QIcon(QPixmap(p))

class CardButton(QPushButton):
    def __init__(self, rank, suit, parent=None):
        super().__init__(parent)
        self.rank, self.suit = rank, suit
        self.setIcon(_icon_for(rank, suit))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background-color: transparent; padding:0px; margin:0px; border:none;")
    def resizeEvent(self, ev):
        try:
            self.setIconSize(ev.size())
        except Exception:
            pass
        return super().resizeEvent(ev)

class CardPicker(QDialog):
    FIXED_WIDTH = 220  # px, as requested
    def __init__(self, parent=None, pick_two=False, used_cards=None):
        super().__init__(parent)
        self.setWindowTitle("Kártyaválasztó")
        self.setModal(True)
        self.selected = None
        self._pick_two = bool(pick_two)
        self._sel = []  # for two-card selection
        self._used = set((used_cards or set()))
        # background + gutters
        self.setStyleSheet("background-color: #1e2a36;")
        g = QGridLayout(self)
        g.setContentsMargins(2,2,2,2)
        g.setHorizontalSpacing(2)
        g.setVerticalSpacing(2)
        # grid 13x4
        for r, rank in enumerate(RANKS):
            for c, suit in enumerate(SUITS):
                b = CardButton(rank, suit, self)
                code = (rank + suit).upper()
                if code in self._used:
                    try:
                        b.setEnabled(False)
                        b.setStyleSheet(b.styleSheet() + '; opacity: 0.4;')
                    except Exception:
                        pass
                b.clicked.connect(lambda _, rr=rank, ss=suit: self._on_click(rr+ss, b))
                g.addWidget(b, r, c)
        # position on first show
        QTimer.singleShot(0, self._reposition_docked)

    def _pick(self, card):
        self.selected = card
        self.accept()

    def _reposition_docked(self):
        try:
            par = self.parent()
            if par is None:
                return
            # Parent frame geometry (includes titlebar)
            pg = par.frameGeometry()
            # Our frame deltas
            fg = self.frameGeometry()
            g  = self.geometry()
            delta_top = fg.top() - g.top()
            delta_total = fg.height() - g.height()
            # Align frame tops and heights
            target_frame_top = pg.top()
            target_frame_h   = pg.height()
            target_client_y = target_frame_top - delta_top
            target_client_h = max(200, target_frame_h - delta_total)
            x = pg.right() + 1
            self.setGeometry(x, target_client_y, self.FIXED_WIDTH, target_client_h)
            self.setMinimumSize(self.FIXED_WIDTH, target_client_h)
        except Exception:
            pass

    def _on_click(self, card, btn):
        try:
            if not self._pick_two:
                self._pick(card)
                return
            # two-card mode
            if card in self._sel:
                return
            self._sel.append(card)
            btn.setEnabled(False)
            if len(self._sel) >= 2:
                self.selected = self._sel[:2]
                self.accept()
        except Exception:
            pass
