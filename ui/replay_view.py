
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QGroupBox, QSizePolicy

class ReplayView(QWidget):
    stepChanged = pyqtSignal(int)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.actions = []  # list of dicts: {street,pos,move,size}
        self.players = {}  # pos -> {name, stack}
        self.cur = -1
        self.stepChanged.emit(self.cur)
        self.pot = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(900)
        self._timer.timeout.connect(self.next_step)

        lay = QVBoxLayout(self)
        try:
            lay.setContentsMargins(6,4,6,4)
            lay.setSpacing(4)
        except Exception:
            pass
        lay.setContentsMargins(6,6,6,6)
        lay.setSpacing(6)

        # Info header
        self.lbl_title = QLabel("Replayer")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(self.lbl_title)

        # Players table
        self.tbl = QTableWidget(0, 3, self)
        self.tbl.setHorizontalHeaderLabels(["Pozíció", "Név", "Stack (BB)"])
        self.tbl.verticalHeader().setVisible(False)
        # Hide/collapse the redundant table (kept in memory so logic won't break)
        self.tbl.setVisible(False)
        self.tbl.setFixedHeight(0)
        self.tbl.setMaximumHeight(0)
        try:
            self.tbl.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        except Exception:
            pass
        # DO NOT add it to the layout to free space
        # # table removed from layout per user request

        # Current step box
        self._step_box = QGroupBox("Lépés")
        inner = QVBoxLayout(self._step_box)
        try:
            self._step_box.setVisible(False)
            self._step_box.setFixedHeight(0)
            self._step_box.setMaximumHeight(0)
        except Exception:
            pass
        self.lbl_step = QLabel("–", self)
        self.lbl_pot = QLabel("Pot: 0.0 BB", self)
        inner.addWidget(self.lbl_step)
        inner.addWidget(self.lbl_pot)
        # # lay.addWidget(self._step_box)  # removed per user request  # removed per user request

        # Controls
        ctrl = QHBoxLayout()
        self.btn_prev = QPushButton("◀ Előző")
        self.btn_next = QPushButton("Következő ▶")
        self.btn_play = QPushButton("Lejátszás")
        ctrl.addWidget(self.btn_prev)
        ctrl.addWidget(self.btn_play)
        ctrl.addWidget(self.btn_next)
        lay.addLayout(ctrl)

        self.btn_prev.clicked.connect(self.prev_step)
        self.btn_next.clicked.connect(self.next_step)
        self.btn_play.clicked.connect(self.toggle_play)

    def set_state(self, players: dict, actions: list):
        from copy import deepcopy
        self._base_players = deepcopy(players or {})
        self.players = deepcopy(players or {})
        self.actions = actions or []
        self.cur = -1
        self.stepChanged.emit(self.cur)
        self.pot = 0.0
        # fill table
        self.tbl.setRowCount(0)
        order = ["UTG","HJ","CO","BTN","SB","BB"]
        for pos in order:
            p = self.players.get(pos) or {"name":"", "stack":0}
            r = self.tbl.rowCount()
            self.tbl.insertRow(r)
            self.tbl.setItem(r, 0, QTableWidgetItem(pos))
            self.tbl.setItem(r, 1, QTableWidgetItem(p.get("name","")))
            self.tbl.setItem(r, 2, QTableWidgetItem(f"{float(p.get('stack',0) or 0):.2f}"))
        self.update_step_label(); self.stepChanged.emit(self.cur)

    def toggle_play(self):
        if self._timer.isActive():
            self._timer.stop()
            self.btn_play.setText("Lejátszás ⏵")
        else:
            self._timer.start()
            self.btn_play.setText("Szünet ⏸")

    def prev_step(self):
        if self.cur >= 0:
            self.cur -= 1
            self.recompute_pot()
            self.update_step_label(); self.stepChanged.emit(self.cur)

    def next_step(self):
        if self.cur + 1 < len(self.actions):
            self.cur += 1
            self.apply_action(self.actions[self.cur])
            self.update_step_label(); self.stepChanged.emit(self.cur)
        else:
            self._timer.stop()
            self.btn_play.setText("Lejátszás ⏵")

    def recompute_pot(self):
        from copy import deepcopy
        self.players = deepcopy(getattr(self, '_base_players', self.players))
        self.pot = 0.0
        if not isinstance(self.actions, list):
            self.lbl_pot.setText(f"Pot: {self.pot:.2f} BB"); return
        limit = max(0, self.cur + 1)
        for i, a in enumerate(self.actions):
            mv = str(a.get("move","")).lower()
            try: sz = float(a.get("size") or a.get("size_bb") or 0.0)
            except Exception: sz = 0.0
            if self.cur < 0:
                if ('post' in mv) or (mv in ("ante","straddle")):
                    self.pot += max(0.0, sz)
                    try:
                        pos = a.get('pos','')
                        cur = float(self.players.get(pos,{}).get('stack',0) or 0)
                        self.players[pos]['stack'] = max(0.0, cur - max(0.0, sz))
                    except Exception:
                        pass
            else:
                if i >= limit: break
                if ('post' in mv) or (mv in ("ante","straddle","bets","raises","opens","all-in","calls")):
                    self.pot += max(0.0, sz)
                    try:
                        pos = a.get('pos','')
                        cur = float(self.players.get(pos,{}).get('stack',0) or 0)
                        self.players[pos]['stack'] = max(0.0, cur - max(0.0, sz))
                    except Exception:
                        pass
        self.lbl_pot.setText(f"Pot: {self.pot:.2f} BB")


    def apply_action(self, a):
        # recompute globally from base; don't mutate incrementally
        size = float(a.get("size") or a.get("size_bb") or 0.0)
        move = a.get("move","")
        pos = a.get("pos","")
        if (("post" in move.lower()) or (move in ("ante","straddle","bets","raises","opens","all-in","calls"))):
            self.pot += size
            if pos in self.players:
                try:
                    cur = float(self.players[pos].get("stack",0) or 0)
                    self.players[pos]["stack"] = max(0.0, cur - size)
                except Exception:
                    pass
        self.recompute_pot()
        # update UI stacks
        for r in range(self.tbl.rowCount()):
            p = self.tbl.item(r,0).text()
            if p == pos:
                self.tbl.setItem(r,2, QTableWidgetItem(f"{float(self.players[p].get('stack',0) or 0):.2f}"))
                break

    def update_step_label(self):
        if self.cur < 0:
            self.lbl_step.setText("Kezdő állapot")
            self.lbl_pot.setText("Pot: 0.0 BB")
        else:
            a = self.actions[self.cur]
            sz = a.get("size")
            disp = f"{a.get('street','')} – {a.get('pos','')}: {a.get('move','')}" + (f" {sz} BB" if sz else "")
            self.lbl_step.setText(disp)
        self.recompute_pot()
