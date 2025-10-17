
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QSizePolicy,
    QFileDialog, QLabel, QSlider, QDoubleSpinBox, QRadioButton, QButtonGroup, QGroupBox
)
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QRect, QSize

LABELS = ["A","K","Q","J","T","9","8","7","6","5","4","3","2"]
ACTIONS = ["RFI","Call","3Bet","4Bet","5Bet","FREQ"]
PROFILES = ["A","B","C","D","E"]

ACTION_COLORS = {
    "RFI": QColor(0,114,255,255),     # kék
    "Call": QColor(0,176,80,255),     # zöld
    "3Bet": QColor(220,53,69,255),    # piros
    "4Bet": QColor(128,0,32,255),     # bordó
    "5Bet": QColor(90,90,90,255),     # sötétszürke
}

def hand_name(r: int, c: int) -> str:
    col = LABELS[c]; row = LABELS[r]
    if r == c:
        return row + col  # párok pl. AA
    if r < c:
        return row + col + "o"  # felső háromszög: offsuit
    return col + row + "s"      # alsó háromszög: suited


class RangeCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.selected_by_action = {a: set() for a in ACTIONS}
        for _p in ["A","B","C","D","E"]:
            self.selected_by_action[f"FREQ_{_p}"] = set()
        self.current_action = "RFI"
        self.grid_bounds = None
        self.grid_rects = {}  # hand -> QRect

    def sizeHint(self) -> QSize: return QSize(640, 480)
    def minimumSizeHint(self) -> QSize: return QSize(320, 240)

    def resizeEvent(self, ev):
        try: self._compute_grid()
        except Exception: pass
        return super().resizeEvent(ev)

    def _compute_grid(self):
        w, h = self.width(), self.height()
        margin = 40
        L, T = margin, margin
        R, B = w - margin, h - margin
        cols = rows = 14
        cw = (R - L) / cols; ch = (B - T) / rows
        self.grid_bounds = QRect(L, T, int(R-L), int(B-T))
        self.grid_rects.clear()
        for r in range(13):
            for c in range(13):
                gx, gy = c + 1, r + 1
                x1 = int(L + gx * cw); y1 = int(T + gy * ch)
                x2 = int(L + (gx+1) * cw); y2 = int(T + (gy+1) * ch)
                self.grid_rects[hand_name(r,c)] = QRect(x1, y1, x2-x1, y2-y1)

    def mousePressEvent(self, ev):
        if ev.button() != Qt.MouseButton.LeftButton: return
        if not self.grid_rects: self._compute_grid()
        pos = ev.position().toPoint()
        for hand, rc in self.grid_rects.items():
            if rc.contains(pos):
                aset = self.selected_by_action.get(self.current_action, set())
                if hand in aset: aset.remove(hand)
                else: aset.add(hand)
                self.selected_by_action[self.current_action] = aset
                self.update(rc)
                break

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()
        p.fillRect(0,0,w,h,QColor(13,19,28))

        if self.grid_bounds is None or not self.grid_rects: self._compute_grid()

        rect = self.grid_bounds
        L, T, W, H = rect.x(), rect.y(), rect.width(), rect.height()
        cols = rows = 14
        cw = W / cols; ch = H / rows

        # keret + rács
        p.setPen(QPen(QColor(50,65,80),2)); p.drawRect(rect)
        p.setPen(QPen(QColor(42,54,70),1))
        for i in range(cols+1):
            x = int(L + i*cw); p.drawLine(x, T, x, T+H)
        for j in range(rows+1):
            y = int(T + j*ch); p.drawLine(L, y, L+W, y)

        # fejlécek
        font = p.font(); font.setBold(True); font.setPointSizeF(max(9.0, min(cw,ch)*0.25)); p.setFont(font)
        def center(txt, rct): p.setPen(QColor(210,220,235)); p.drawText(rct, Qt.AlignmentFlag.AlignCenter, txt)
        for i, lab in enumerate(LABELS):
            center(lab, QRect(int(L + (i+1)*cw), T, int(cw), int(ch)))
            center(lab, QRect(int(L), int(T + (i+1)*ch), int(cw), int(ch)))

        # színezés

        # színezés (mindig együtt: akciók + frekvenciális overlay)
        # 1) Normál akciók (teljes cella, FREQ kivételével)
        for act, aset in self.selected_by_action.items():
            if act == "FREQ": 
                continue
            base = ACTION_COLORS.get(act, QColor(200,200,200))
            col = QColor(base.red(), base.green(), base.blue(), 205)
            for hand in aset:
                rc = self.grid_rects.get(hand)
                if rc: 
                    p.fillRect(rc, col)

        # 2) Frekvenciális overlay – MINDEN profil (A–E) egyszerre, azonos intenzitással
        order = ["RFI","Call","3Bet","4Bet","5Bet"]
        parent = self.parent()
        for prof in ["A","B","C","D","E"]:
            freq_hands = set(self.selected_by_action.get(f"FREQ_{prof}", set()))
            if not freq_hands:
                continue
            prof_freqs = getattr(parent, 'freq_profiles', {}).get(prof, {a:0.0 for a in order})
            parts = [(a, max(0.0, float(prof_freqs.get(a,0.0))) / 100.0) for a in order]
            for hand in freq_hands:
                rc = self.grid_rects.get(hand)
                if rc is None:
                    continue
                left, top = rc.left()+1, rc.top()+1
                width, height = rc.width()-2, rc.height()-2
                runx = left
                for a, frac in parts:
                    if frac <= 0:
                        continue
                    wseg = int(round(width*frac))
                    if wseg <= 0:
                        continue
                    seg = QRect(runx, top, wseg, height)
                    base = ACTION_COLORS.get(a, QColor(200,200,200))
                    col = QColor(base.red(), base.green(), base.blue(), 205)  # stabil, erős alpha
                    p.fillRect(seg, col)
                    runx += wseg
        # feliratok felülre
        font.setBold(False); font.setPointSizeF(max(8.0, min(cw,ch)*0.22)); p.setFont(font); p.setPen(QColor(230,235,240))
        for r in range(13):
            for c in range(13):
                name = hand_name(r,c); rc = self.grid_rects[name]
                p.drawText(rc, Qt.AlignmentFlag.AlignCenter, name)


class RangeSelectorDialog(QDialog):
    def _uncheck_group(self, group):
        try:
            for b in group.buttons():
                bs = b.blockSignals(True)
                try:
                    b.setChecked(False)
                finally:
                    b.blockSignals(bs)
        except Exception:
            pass

    def _set_freq_value_safe(self, act: str, val: float):
        val = max(0.0, min(100.0, float(val)))
        s = self.slider_map.get(act); sp = self.spin_map.get(act)
        if s is None or sp is None: return
        bs, bsp = s.blockSignals(True), sp.blockSignals(True)
        try:
            s.setValue(int(round(val)))
            sp.setValue(float(val))
        finally:
            s.blockSignals(bs); sp.blockSignals(bsp)
        cur = self.freq_profiles.setdefault(self.active_freq, {a:0.0 for a in ["RFI","Call","3Bet","4Bet","5Bet"]})
        cur[act] = float(val)

    def __init__(self, parent=None, initial=None, title="Range kiválasztó"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.canvas = RangeCanvas(self)
        if initial: self.canvas.selected_by_action["RFI"] = set(initial)

        # jobboldali panel: akciók + csúszkák
        right = QVBoxLayout()
        # Egyetlen exkluzív csoport az összes akció gombnak (RFI/Call/3Bet/4Bet/5Bet + FREQ A–E)
        self.action_group = QButtonGroup(self); self.action_group.setExclusive(True)

        actions_col = QVBoxLayout()
        act_head = QLabel("Akciók")
        try: act_head.setStyleSheet("color:#9ecbff; font-weight:600;")
        except Exception: pass
        actions_col.addWidget(act_head)
        for act in ["RFI","Call","3Bet","4Bet","5Bet"]:
            rb = QRadioButton(act)
            if act == "RFI": rb.setChecked(True)
            self.action_group.addButton(rb); rb.setProperty("action", act); actions_col.addWidget(rb)
            rb.toggled.connect(lambda state, a=act: state and self._on_action(a))

        freq_col = QVBoxLayout()
        head = QLabel("Frekvenciális")
        try: head.setStyleSheet("color:#9ecbff; font-weight:600;")
        except Exception: pass
        freq_col.addWidget(head)
        for lab in ["A","B","C","D","E"]:
            rb = QRadioButton(lab); rb.setProperty("action", f"FREQ_{lab}")
            self.action_group.addButton(rb); freq_col.addWidget(rb)
            rb.toggled.connect(lambda state, l=lab: state and self._on_action(f"FREQ_{l}"))

        row = QHBoxLayout(); row.addLayout(actions_col); row.addSpacing(12); row.addLayout(freq_col)
        right.addLayout(row)
        right.addSpacing(8)
        

        self.freq_profiles = {k: {a: 0.0 for a in ["RFI","Call","3Bet","4Bet","5Bet"]} for k in PROFILES}
        self.active_freq = "A"
        self.slider_map = {}; self.spin_map = {}
        for act in ["RFI","Call","3Bet","4Bet","5Bet"]:
            gb = QGroupBox(f"{act} frekvencia (%)")
            hl = QHBoxLayout()
            s = QSlider(Qt.Orientation.Horizontal); s.setRange(0,100); s.setValue(0)
            sp = QDoubleSpinBox(); sp.setDecimals(1); sp.setRange(0.0,100.0); sp.setSingleStep(0.5); sp.setValue(0.0)
            s.valueChanged.connect(lambda v, a=act: (self.spin_map[a].setValue(float(v)), self._on_freq_change(a, float(v))))
            sp.valueChanged.connect(lambda v, a=act: (self.slider_map[a].setValue(int(v)), self._on_freq_change(a, float(v))))
            hl.addWidget(s); hl.addWidget(sp); gb.setLayout(hl); right.addWidget(gb)
            self.slider_map[act] = s; self.spin_map[act] = sp
        right.addStretch(1)
        # --- VISSZATÖLTÉS: ha 'initial' teljes szerkezet (by_action + freqs), akkor töltsük vissza ---
        try:
            if isinstance(initial, dict) and ('by_action' in initial or 'by_freq' in initial):
                # 1) Akciónkénti handek visszaállítása
                for a in ACTIONS:
                    hands = set(initial.get('by_action', {}).get(a, []))
                    self.canvas.selected_by_action[a] = set(hands)
                # 2) Frekvenciális profilok és handek visszaállítása
                by_freq = initial.get('by_freq', {})
                for p in PROFILES:
                    self.canvas.selected_by_action[f"FREQ_{p}"] = set(by_freq.get(p, []))
                profs = initial.get('freq_profiles', {})
                for p in PROFILES:
                    dst = self.freq_profiles.setdefault(p, {a:0.0 for a in ["RFI","Call","3Bet","4Bet","5Bet"]})
                    for a in ["RFI","Call","3Bet","4Bet","5Bet"]:
                        dst[a] = float(profs.get(p, {}).get(a, 0.0))
                # 3) Sliderek/szpinboxok frissítése a beállított értékekre
                self.active_freq = 'A'
                prof = self.freq_profiles.get(self.active_freq, {k:0.0 for k in ["RFI","Call","3Bet","4Bet","5Bet"]})
                for a,v in prof.items():
                    if a in self.slider_map: self.slider_map[a].setValue(int(round(float(v))))
                    if a in self.spin_map: self.spin_map[a].setValue(float(v))
                # 4) Vászon redraw
                self.canvas.update()
            elif isinstance(initial, (list, tuple, set)):
                # Visszafelé kompatibilis: csak RFI listát kaptunk
                self.canvas.selected_by_action["RFI"] = set(initial)
                self.canvas.update()
        except Exception:
            pass


        # alul gombok
        btns = QHBoxLayout()
        ok = QPushButton("OK"); cancel = QPushButton("Mégse"); clear = QPushButton("Törlés")
        ok.clicked.connect(self.accept); cancel.clicked.connect(self.reject); clear.clicked.connect(self._on_clear)
        btns.addWidget(clear); btns.addStretch(1); btns.addWidget(ok); btns.addWidget(cancel)
        # gombsor áthelyezése a jobb oldali panel aljára
        right.addSpacing(8)
        
        right.addLayout(btns)

        # fő layout
        root = QHBoxLayout(self)
        root.addWidget(self.canvas, 3)
        rightw = QWidget(); rightw.setLayout(right); rightw.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        root.addWidget(rightw, 0)

    def _on_action(self, a: str):
        if a.startswith("FREQ_"):
            self.active_freq = a.split("_",1)[1]
            self.canvas.current_action = a  # e.g. FREQ_A
            prof = self.freq_profiles.get(self.active_freq, {k:0.0 for k in ["RFI","Call","3Bet","4Bet","5Bet"]})
            for k,v in prof.items():
                self._set_freq_value_safe(k, float(v))
        else:
            self.canvas.current_action = a
        self.canvas.update()

    def _on_freq_change(self, act: str, v: float):
        bucket = ["RFI","Call","3Bet","4Bet","5Bet"]
        cur = self.freq_profiles.get(self.active_freq, {a:0.0 for a in bucket})
        others = sum(float(cur.get(a, 0.0)) for a in bucket if a != act)
        allowed = max(0.0, 100.0 - others)
        v_capped = min(max(0.0, float(v)), allowed)
        self._set_freq_value_safe(act, v_capped)
        self.canvas.update()

    def accept(self):
        try:
            by_action = {a: sorted(list(self.canvas.selected_by_action.get(a, set()))) for a in ["RFI","Call","3Bet","4Bet","5Bet"]}
            by_freq = {p: sorted(list(self.canvas.selected_by_action.get(f"FREQ_{p}", set()))) for p in PROFILES}
            result = {
                "by_action": by_action,
                "by_freq": by_freq,
                "freq_profiles": {p: {k: float(v) for k,v in self.freq_profiles.get(p, {}).items()} for p in PROFILES}
            }
            self.result_all = result
        except Exception:
            self.result_all = None
        return super().accept()

    def _on_clear(self):
        self.canvas.selected_by_action = {a: set() for a in ACTIONS}
        self.canvas.update()

    @property
    def selected(self) -> list[str]:
        # VISSZAMENŐLEGES KOMPATIBILITÁS: marad az RFI lista
        return sorted(list(self.canvas.selected_by_action.get("RFI", set())))

    @property
    def selected_all(self):
        # Minden akció set + frekvenciák egyben
        by_action = {a: sorted(list(self.canvas.selected_by_action.get(a, set()))) for a in ACTIONS}
        return {"by_action": by_action, "freqs": {k: float(v) for k,v in self.freqs.items() if k != "FREQ"}}

    def accept(self):
        try:
            by_action = {a: sorted(list(self.canvas.selected_by_action.get(a, set()))) for a in ["RFI","Call","3Bet","4Bet","5Bet"]}
            by_freq = {p: sorted(list(self.canvas.selected_by_action.get(f"FREQ_{p}", set()))) for p in PROFILES}
            result = {
                "by_action": by_action,
                "by_freq": by_freq,
                "freq_profiles": {p: {k: float(v) for k,v in self.freq_profiles.get(p, {}).items()} for p in PROFILES}
            }
            self.result_all = result
        except Exception:
            self.result_all = None
        return super().accept()