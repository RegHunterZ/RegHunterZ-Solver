from PyQt6.QtCore import QPointF
from PyQt6 import QtWidgets, QtGui, QtCore

RANKS = "AKQJT98765432"

class RangePainter(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        self.grid_color = QtGui.QColor(40,40,40)
        self.cell_color = QtGui.QColor(22,22,22)
        self.line_color = QtGui.QColor(70,70,70)
        self.pen = QtGui.QPen(self.line_color, 1)
        self.font = QtGui.QFont("Segoe UI", 11)
        self.cells = {}

        # top-bar
        lay = QtWidgets.QVBoxLayout(self)
        hb = QtWidgets.QHBoxLayout()
        self.btn_demo = QtWidgets.QPushButton("Demo range kirajzolása")
        self.btn_clear = QtWidgets.QPushButton("CLEAN")
        hb.addWidget(self.btn_demo, 1)
        hb.addWidget(self.btn_clear, 1)
        lay.addLayout(hb)
        self.canvas = Canvas(self)
        lay.addWidget(self.canvas, 1)

        self.btn_demo.clicked.connect(self.draw_demo)
        self.btn_clear.clicked.connect(self.canvas.clear_all)

    def draw_demo(self):
        # simple diagonal for demo
        for i, r in enumerate(RANKS):
            key = f"{r}{r}"
            self.canvas.set_cell(i, i, True)

class Canvas(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(520)
        self.active = set()

    def sizeHint(self):
        return QtCore.QSize(960, 520)

    def clear_all(self):
        self.active.clear()
        self.update()

    def set_cell(self, i, j, on=True):
        if on: self.active.add((i,j))
        else: self.active.discard((i,j))
        self.update()

    def paintEvent(self, e):
        p = QtGui.QPainter(self)
        rect = self.rect()
        p.fillRect(rect, QtGui.QColor(20,20,20))
        # header
        ranks = RANKS
        n = len(ranks)
        margin = 48
        W = rect.width()-margin; H = rect.height()-margin
        cw = W/n; ch = H/n
        # headers
        p.setPen(QtGui.QPen(QtGui.QColor(180,180,180)))
        f = p.font(); f.setPointSize(12); p.setFont(f)
        for i,c in enumerate(ranks):
            p.drawText(int(margin + i*cw + cw/2 - 6), int(24), c)
            p.drawText(int(14), int(margin + i*ch + ch/2 + 6), c)
        # grid
        p.setPen(QtGui.QPen(QtGui.QColor(60,60,60)))
        for i in range(n+1):
            p.drawLine(QPointF(float(margin), float(margin + i*ch)), QPointF(float(margin+W), float(margin + i*ch)))
            p.drawLine(QPointF(float(margin + i*cw), float(margin)), QPointF(float(margin + i*cw), float(margin+H)))
        # cells
        for (i,j) in self.active:
            cell = QtCore.QRectF(margin + i*cw+1, margin + j*ch+1, cw-2, ch-2)
            p.fillRect(cell, QtGui.QColor(30,120,90))
