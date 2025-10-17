from ai_coach.inline_range_hh import inject_ranges_into_hh
import integrations.range_buttons_inject as _rng_inj
from PyQt6.QtWidgets import (QFrame, 
    QDialog, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QHBoxLayout,
    QPushButton, QTabWidget, QWidget, QComboBox, QFormLayout, QGroupBox, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from .card_picker import CardPicker
from .range_selector import RangeSelectorDialog

POSITIONS = ["UTG", "HJ", "CO", "BTN", "SB", "BB"]
ACTIONS = ["—", "post", "opens", "raises", "bets", "calls", "checks", "folds", "all-in"]

def _card_hint() -> str:
    return "pl. Ah, Kd, Ts..."


def _flatten_slot_union(slot_range) -> set:
    """Accepts either a list of hands or a dict result_all and returns a set of hands.
    - dict with 'by_action': union all action lists
    - dict with 'by_freq': also union profile lists
    - plain list/tuple/set: treated as RFI-only list
    """
    try:
        if isinstance(slot_range, dict):
            u = set()
            if 'by_action' in slot_range and isinstance(slot_range['by_action'], dict):
                for lst in slot_range['by_action'].values():
                    try:
                        u.update(lst or [])
                    except Exception:
                        pass
            if 'by_freq' in slot_range and isinstance(slot_range['by_freq'], dict):
                for lst in slot_range['by_freq'].values():
                    try:
                        u.update(lst or [])
                    except Exception:
                        pass
            return u
        # legacy list
        return set(slot_range or [])
    except Exception:
        return set()


def _migrate_by_slot_keys(ranges_dict: dict) -> dict:
    """
    Ha a 'by_slot' kulcsok régi, instabil azonosítók (btn_...), alakítsuk át stabil 'POS_slotX' formára.
    Megőrzi az akciónkénti range-eket, FREQ részre nincs beavatkozás.
    """
    try:
        out = {}
        for pos, pdata in (ranges_dict or {}).items():
            if not isinstance(pdata, dict):
                out[pos] = pdata
                continue
            by_slot = dict(pdata.get("by_slot", {}))
            # ha már stabil kulcsok vannak, hagyjuk
            if all(isinstance(k, str) and "_slot" in k for k in by_slot.keys()):
                out[pos] = pdata
                continue
            # egyébként sorba rendezzük és slot0, slot1 ... kulccsal újraindexelünk
            new_by_slot = {}
            idx = 0
            for k, v in by_slot.items():
                new_by_slot[f"{pos}_slot{idx}"] = v
                idx += 1
            # ha nem volt by_slot, de van by_action (legacy), betesszük slot0-ba
            if not new_by_slot and "by_action" in pdata:
                new_by_slot[f"{pos}_slot0"] = {"action": "LEGACY", "range": {"by_action": pdata.get("by_action", {})}}
            new_pdata = dict(pdata)
            new_pdata["by_slot"] = new_by_slot
            out[pos] = new_pdata
        return out
    except Exception:
        return ranges_dict

class StreetForm(QWidget):
    def _owner(self):
        w = self.parent()
        try:
            # Walk up until a widget that has pick_range_for_action
            while w is not None and not hasattr(w, 'pick_range_for_action'):
                w = w.parent()
        except Exception:
            pass
        return w
    def sizeHint(self):
        from PyQt6.QtCore import QSize
        return QSize(10, 20)
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.rows = {}
        lay = QFormLayout(self)
        lay.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # ---- FIX: bal oldali címkeoszlop rögzítése ----
        lay.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        # automatikus szélesség (legalább 300px); írhatod ide fixre is: self._pos_label_w = 900
        self._pos_label_w = max(25, self.fontMetrics().horizontalAdvance("BB:") + 12)
        # -----------------------------------------------

        # öt akció-slot minden pozícióhoz
        SLOT_COUNT = 5
        for pos in POSITIONS:
            cont = QWidget(); cont.setLayout(QHBoxLayout()); cont.layout().setContentsMargins(0,0,0,0)
            pairs = []
            for i in range(SLOT_COUNT):
                cb = _compact(QComboBox()); cb.addItems(ACTIONS)
                cb.setFixedWidth(60)
                sz = _compact(QLineEdit()); sz.setPlaceholderText("méret BB (opcionális)")
                sz.setFixedWidth(30)   # <<< FIX: minden "méret BB" mező fixen 20px
                cont.layout().addWidget(cb, 2); cont.layout().addWidget(sz, 1)
                _rb = QPushButton("R"); _rb.setFixedSize(24,24); _rb.setToolTip("Range kiválasztó")
                _rb.clicked.connect(lambda _, pp=pos, combo=cb: self._owner().pick_range_for_action(pp, combo.currentText()))
                cont.layout().addWidget(_rb, 0)
                try:
                    _rb.setProperty("slot_index", i)
                    _rb.setProperty("pos", pos)
                except Exception:
                    pass
                pairs.append((cb, sz))
                if i < SLOT_COUNT-1:
                    from PyQt6.QtWidgets import QLabel as _QLabel
                    sep = _QLabel("  "); cont.layout().addWidget(sep)

            # ---- FIX: címkét fix szélességgel adjuk a sorhoz ----
            lbl = QLabel(pos + ":")
            lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
            lbl.setMinimumWidth(self._pos_label_w)
            lay.addRow(lbl, cont)
            # -----------------------------------------------------

            self.rows[pos] = pairs

    
    def to_lines(self):
        """Időrendi sorrend: slot 0..n, minden körben UTG→BB pozíciók.
        Minden elemnél megtartjuk a méretet is (ha megadva)."""
        lines = []
        try:
            slot_count = len(self.rows.get('UTG', []))
        except Exception:
            slot_count = 0
        if slot_count <= 0:
            return lines
        for slot in range(slot_count):
            for pos in POSITIONS:
                try:
                    pair_list = self.rows.get(pos, [])
                    if slot >= len(pair_list):
                        continue
                    cb, sz = pair_list[slot]
                    act = cb.currentText()
                    if act and act != "—":
                        size = (sz.text() or "").strip()
                        if act in ("bets","raises","calls","all-in","opens") and size:
                            lines.append(f"{pos} {act} {size} BB")
                        else:
                            lines.append(f"{pos} {act}")
                except Exception:
                    pass
        return lines
        for slot in range(slot_count):
            for pos in POSITIONS:
                try:
                    pair_list = self.rows.get(pos, [])
                    if slot >= len(pair_list):
                        continue
                    cb, sz = pair_list[slot]
                    act = cb.currentText()
                    if act and act != "—":
                        size = (sz.text() or "").strip()
                        if act in ("bets","raises","calls","all-in","opens") and size:
                            lines.append(f"{pos} {act} {size} BB")
                        else:
                            lines.append(f"{pos} {act}")
                except Exception:
                    pass
        return lines
def _compact(w):
    try:
        w.setFixedHeight(22)
    except Exception:
        pass
    return w



    def load_struct(self, data: dict):
        """
        Visszatölt mindent a struktúrából (stacks, hole_cards, board, actions, ranges).
        Nem hoz létre új sort a HH-hoz, csak a dialógus mezőit állítja be.
        """
        try:
            data = data or {}
            # stacks
            stacks = data.get("stacks", {}) or {}
            for pos, edit in self.stack_edits.items():
                try:
                    val = stacks.get(pos, "")
                    if val is not None:
                        edit.setText(str(val))
                except Exception:
                    pass
            # hole cards
            hole = data.get("hole_cards", {}) or {}
            for pos, cards in hole.items():
                try:
                    c1, c2 = self.card_edits[pos]
                    if isinstance(cards, (list, tuple)) and len(cards) >= 2:
                        c1.setText(self._fmt_card_ui(cards[0]))
                        c2.setText(self._fmt_card_ui(cards[1]))
                except Exception:
                    pass
            # board
            board = data.get("board", {}) or {}
            try:
                fl = board.get("flop", []) or []
                if len(fl) >= 1: self.flop1.setText(self._fmt_card_ui(fl[0]))
                if len(fl) >= 2: self.flop2.setText(self._fmt_card_ui(fl[1]))
                if len(fl) >= 3: self.flop3.setText(self._fmt_card_ui(fl[2]))
                if board.get("turn"): self.turn.setText(self._fmt_card_ui(board.get("turn")))
                if board.get("river"): self.river.setText(self._fmt_card_ui(board.get("river")))
            except Exception:
                pass
            # actions (csak combók/szövegek visszaállítása, opcionális)
            try:
                amap = {"preflop": self.pre_form, "flop": self.flop_form, "turn": self.turn_form, "river": self.river_form}
                for street, sform in amap.items():
                    for pos in POSITIONS:
                        cb, sz = sform.rows[pos]
                        # alapállapot
                        cb.setCurrentIndex(0); sz.setText("")
                acts = data.get("actions", {}) or {}
                for street, sform in amap.items():
                    for item in acts.get(street, []) or []:
                        try:
                            pos = item.get("pos"); act = item.get("action"); size = item.get("size_bb")
                            cb, sz = sform.rows.get(pos, (None,None))
                            if cb: 
                                # állítsuk be a megfelelő action-t, ha létezik a listában
                                for i in range(cb.count()):
                                    if cb.itemText(i) == act:
                                        cb.setCurrentIndex(i); break
                            if sz and size not in (None, ""):
                                sz.setText(str(size))
                        except Exception:
                            pass
            except Exception:
                pass
            # ranges
            try:
                rg = _migrate_by_slot_keys(data.get("ranges", {}))
                if isinstance(rg, dict):
                    self.ranges = rg
                    # frissítsük a számlálókat
                    for pos in POSITIONS:
                        if pos in self.range_labels:
                            self._update_range_label(pos)
            except Exception:
                pass
        except Exception:
            pass
    
class FlopPicker(QDialog):
    FIXED_WIDTH = 220
    def __init__(self, parent=None, used_cards=None):
        super().__init__(parent)
        from PyQt6.QtCore import QTimer
        from .card_picker import RANKS, SUITS, CardButton
        self.setWindowTitle("Kártyaválasztó")
        self.setModal(True)
        self.selected = []
        used = set(str(c).strip().upper() for c in (used_cards or []) if c)
        self.setStyleSheet("background-color: #1e2a36;")
        g = QGridLayout(self); g.setContentsMargins(2,2,2,2); g.setHorizontalSpacing(2); g.setVerticalSpacing(2)
        for r, rank in enumerate(RANKS):
            for c, suit in enumerate(SUITS):
                code = f"{rank}{suit}".upper()
                b = CardButton(rank, suit, self)
                if code in used:
                    try:
                        b.setEnabled(False); b.setStyleSheet(b.styleSheet() + '; opacity: 0.4;')
                    except Exception: pass
                b.clicked.connect(lambda _, card=code, btn=b: self._pick(card, btn))
                g.addWidget(b, r, c)
        QTimer.singleShot(0, self._reposition_docked)

    def _reposition_docked(self):
        try:
            target = self.parent() or self
            win = target.window(); pg = win.frameGeometry()
            x = pg.right()
            top = target.mapToGlobal(target.rect().topLeft()).y()
            h = target.rect().height()
            self.setGeometry(x, top, self.FIXED_WIDTH, h)
            self.setMinimumSize(self.FIXED_WIDTH, h)
        except Exception: pass

    def _pick(self, card, btn):
        if card in self.selected: return
        self.selected.append(card)
        try: btn.setEnabled(False)
        except Exception: pass
        if len(self.selected) >= 3: self.accept()

class ManualEntryDialog(QDialog):

    def _normalize_card_edit(self, edit):
        try:
            val = self._fmt_card_ui(edit.text())
            edit.setText(val)
        except Exception:
            pass

    def _fmt_card_ui(self, code: str) -> str:
        try:
            code = (code or "").strip()
            if not code:
                return ""
            rank = code[:-1].upper()
            suit = code[-1].lower()
            return f"{rank}{suit}"
        except Exception:
            return str(code)
    def _dock_right_of_parent(self):
        try:
            parent = self.parent() or getattr(self, '_initial_center_parent', None)
            if parent is None:
                return
            win = parent.window()
            # Use the window's frame geometry to dock outside its right edge
            pg = win.frameGeometry()
            x = pg.right()  # no gap; window border to dialog left edge
            y = pg.top()    # align title bars
            # Adjust for Windows border overlap by +1
            x += 1
            # Keep on-screen
            from PyQt6.QtGui import QGuiApplication
            scr = win.windowHandle().screen().availableGeometry() if win.windowHandle() else QGuiApplication.primaryScreen().availableGeometry()
            if x + self.width() > scr.right():
                x = scr.right() - self.width()
            if y < scr.top():
                y = scr.top()
            self.move(x, y)
        except Exception:
            pass

    def __init__(self, parent=None):
        super().__init__(parent)
        # ensure dialog is modal, stays on top and has a reasonable default size
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.Dialog)
        try:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        except Exception:
            pass
        # center on parent if available
        self._initial_center_parent = parent
        self.setFixedSize(420, 600)
        self.setSizeGripEnabled(False)
        self.setWindowTitle("Manuális bevitel – Stacks, Lapok és Akciók")
        self._dock_right_of_parent()
        # follow parent window moves/resizes
        try:
            win = (parent.window() if parent is not None else None)
            if win is not None:
                win.installEventFilter(self)
        except Exception:
            pass

        try:
            if parent is not None:
                parent_geo = parent.frameGeometry()
                new_x = parent_geo.topRight().x() - self.width()
                new_y = parent_geo.top()
                self.move(new_x, new_y)
        except Exception:
            pass

        self.setFixedSize(750, 500)  # fixed half width as requested

        self.setFixedSize(750, 500)
        try:
            self.setMaximumSize(16777215, 16777215)  # no hard cap
        except Exception:
            pass


        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        grid = QGridLayout(); grid.setHorizontalSpacing(0); grid.setVerticalSpacing(0); grid.setContentsMargins(0,20,0,0)
        self.stack_edits = {}
        self.card_edits = {}
        for i, pos in enumerate(POSITIONS):
            grid.addWidget(QLabel(pos + " Stack (BB):"), i, 0)
            e = QLineEdit(self); e.setPlaceholderText("pl. 100"); e.setText("100"); e.setFixedWidth(64)
            self.stack_edits[pos] = e
            grid.addWidget(e, i, 1)

            c1 = _compact(QLineEdit()); c1.setMaxLength(2); c1.setPlaceholderText(_card_hint()); c1.setFixedWidth(30)
            c2 = _compact(QLineEdit()); c2.setMaxLength(2); c2.setPlaceholderText(_card_hint()); c2.setFixedWidth(30)
            self.card_edits[pos] = (c1, c2)
            card_box = QWidget(); h = QHBoxLayout(); h.setContentsMargins(0,0,0,0); card_box.setLayout(h)
            h.addWidget(QLabel("Lapok:"))
            # két kezdő lap editor
            h.addWidget(c1); h.addWidget(c2)
            # picker gomb
            btn = _compact(QPushButton("Választ")); btn.setFixedWidth(60); btn.clicked.connect(lambda _, pp=pos: self.pick_hole_cards(pp))
            h.addWidget(btn)
            # számláló címke (range összegzés)
            if not hasattr(self, "range_labels"): self.range_labels = {}
            if not hasattr(self, "ranges"): self.ranges = {}
            lbl = QLabel("")
            try:
                lbl.setStyleSheet("color:#9ecbff;")
            except Exception:
                pass
            h.addWidget(lbl)
            self.range_labels[pos] = lbl
            grid.addWidget(card_box, i, 2, 1, 2)
        
        # --- Board kártyák doboz a felső GRID-be integrálva ---
        vsep = QWidget(); vsep.setFixedWidth(6); vsep.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding);
        # elválasztó szín – igazítva az alsó kis négyzethez
        vsep.setStyleSheet("background-color: rgba(255,255,255,0.06);")
        board_box = QGroupBox("Board kártyák")
        board_box.setStyleSheet("QGroupBox{margin-top:0px;padding-top:0px;border:1px solid rgba(255,255,255,0.08);} QGroupBox::title{subcontrol-origin: margin; left:6px; padding:0px 4px; margin:0px;}")
        bb = QGridLayout(board_box); bb.setColumnStretch(0, 0); bb.setColumnStretch(1, 0); bb.setColumnStretch(2, 0); bb.setColumnStretch(3, 0); bb.setHorizontalSpacing(0); bb.setVerticalSpacing(0); bb.setContentsMargins(0,0,0,0)
        self.flop1 = _compact(QLineEdit()); self.flop1.setMaxLength(2); self.flop1.setPlaceholderText(_card_hint()); self.flop1.setFixedWidth(28)
        self.flop2 = _compact(QLineEdit()); self.flop2.setMaxLength(2); self.flop2.setPlaceholderText(_card_hint()); self.flop2.setFixedWidth(28)
        self.flop3 = _compact(QLineEdit()); self.flop3.setMaxLength(2); self.flop3.setPlaceholderText(_card_hint()); self.flop3.setFixedWidth(28)
        _flopRow = QWidget(); _frl = QHBoxLayout(_flopRow); _frl.setContentsMargins(0,0,0,0); _frl.setSpacing(0)
        _frl.addWidget(self.flop1); _frl.addWidget(self.flop2); _frl.addWidget(self.flop3)
        bb.addWidget(QLabel("Flop:"), 0, 0); bb.addWidget(_flopRow, 0, 1, 1, 1, alignment=Qt.AlignmentFlag.AlignLeft)
        self.turn = _compact(QLineEdit()); self.turn.setMaxLength(2); self.turn.setPlaceholderText(_card_hint()); self.turn.setFixedWidth(28)
        bb.addWidget(QLabel("Turn:"), 1, 0); bb.addWidget(self.turn, 1, 1)
        self.river = _compact(QLineEdit()); self.river.setMaxLength(2); self.river.setPlaceholderText(_card_hint()); self.river.setFixedWidth(28)
        bb.addWidget(QLabel("River:"), 2, 0); bb.addWidget(self.river, 2, 1)
        # gombok
        b_f1 = _compact(QPushButton("Választ")); b_f1.setFixedWidth(60); b_f1.clicked.connect(self.pick_flop_triple); bb.addWidget(b_f1,0,4)
        b_t = _compact(QPushButton("Választ")); b_t.setFixedWidth(60); b_t.clicked.connect(lambda: self.pick_card(self.turn)); bb.addWidget(b_t,1,4)
        b_r = _compact(QPushButton("Választ")); b_r.setFixedWidth(60); b_r.clicked.connect(lambda: self.pick_card(self.river)); bb.addWidget(b_r,2,4)
             # a board_box most a GRID-be kerül, közvetlenül a stack/lapok sorok alá
        grid.addWidget(board_box, 0, 4, len(POSITIONS), 2, alignment=Qt.AlignmentFlag.AlignTop)
        lay.addLayout(grid)
        lay.addSpacing(12)
        # (Blinds box removed as per request)

        self.tabs = QTabWidget(self)
        self.pre_form = StreetForm("Preflop", self); self.tabs.addTab(self.pre_form, "Preflop")
        self.flop_form = StreetForm("Flop", self); self.tabs.addTab(self.flop_form, "Flop")
        self.turn_form = StreetForm("Turn", self); self.tabs.addTab(self.turn_form, "Turn")
        self.river_form = StreetForm("River", self); self.tabs.addTab(self.river_form, "River")
        lay.addWidget(self.tabs)

        # --- AUTO: add per-row range buttons ---
        try:
            _rng_inj.attach_per_row_range_buttons(self)
        except Exception:
            pass

        # --- Footer with OK/Cancel ---
        btns = QHBoxLayout(); btns.setContentsMargins(0,8,0,0); btns.setSpacing(10)
        self.btn_ok = _compact(QPushButton("OK – HH generálás")); self.btn_ok.setDefault(True); self.btn_ok.setAutoDefault(True)
        self.btn_cancel = _compact(QPushButton("Mégse")); self.btn_cancel.setAutoDefault(False)
        btns.addStretch(1); btns.addWidget(self.btn_ok); btns.addWidget(self.btn_cancel)
        footer = QWidget(); footer.setFixedHeight(56)
        footer_l = QHBoxLayout(footer); footer_l.setContentsMargins(8,8,8,8); footer_l.addLayout(btns)
        footer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lay.addStretch(1)
        lay.addWidget(footer)
        self.btn_ok.clicked.connect(self.accept); self.btn_cancel.clicked.connect(self.reject)
    def _collect_used_cards(self, exclude_edits=None):
        try:
            excl = set(exclude_edits or [])
        except Exception:
            excl = set()
        used = []
        for pos in POSITIONS:
            c1, c2 = self.card_edits.get(pos, (None, None))
            for w in (c1, c2):
                if (w is None) or (w in excl):
                    continue
                t = (w.text() or "").strip().upper()
                if len(t) >= 2:
                    used.append(t)
        for w in (getattr(self, 'flop1', None), getattr(self, 'flop2', None), getattr(self, 'flop3', None), getattr(self, 'turn', None), getattr(self, 'river', None)):
            try:
                if (w is None) or (w in excl):
                    continue
                t = (w.text() or "").strip().upper()
                if len(t) >= 2:
                    used.append(t)
            except Exception:
                pass
        return set(used)

    def pick_card(self, line_edit: QLineEdit):
        used = self._collect_used_cards(exclude_edits=[line_edit])
        dlg = CardPicker(self, used_cards=used)
        if dlg.exec():
            line_edit.setText(dlg.selected)

    def _preflop_lines_with_ranges(self):
        """Preflop akciók; a range a sor VÉGÉRE kerül (— KEY: [...])."""
        out = []
        try:
            rows_obj = getattr(self, "pre_form", None)
            rows = getattr(rows_obj, "rows", {}) if rows_obj is not None else {}
            sample = rows.get("UTG", [])
            slot_cnt = len(sample) if isinstance(sample, list) else 0
            if slot_cnt <= 0:
                return out
    
            POS = POSITIONS if "POSITIONS" in globals() else ["UTG","HJ","CO","BTN","SB","BB"]
    
            def action_key(act_text: str, raise_count: int, saw_open: bool):
                t = (act_text or "").lower()
                if t in ("opens", "bets"):
                    return "RFI"
                if t == "raises":
                    if raise_count == 0 and not saw_open:
                        return "RFI"
                    keys = ["3Bet","4Bet","5Bet"]
                    return keys[min(raise_count, len(keys)-1)]
                if t == "calls":
                    return "Call"
                return None
    
            rngs = getattr(self, "ranges", {}) or {}
    
            for slot in range(slot_cnt):
                raise_seen = 0
                saw_open = False
                for pos in POS:
                    pair_list = rows.get(pos, [])
                    if slot >= len(pair_list):
                        continue
                    try:
                        cb, sz = pair_list[slot]
                        act = cb.currentText() if hasattr(cb, "currentText") else str(cb)
                        size_txt = sz.text().strip() if hasattr(sz, "text") else str(sz).strip()
                    except Exception:
                        act, size_txt = "", ""
    
                    if not act or act == "—":
                        continue
                    if act.lower() in ("opens", "bets"):
                        saw_open = True
    
                    desc = f"{pos} {act} {size_txt}".strip()
    
                    akey = action_key(act, raise_seen, saw_open)
                    if act.lower() == "raises":
                        raise_seen += 1
    
                    addon = ""
                    try:
                        pos_map = rngs.get(pos, {}) or {}
                        by_action_top = pos_map.get("by_action", {}) or {}
                        by_slot = pos_map.get("by_slot", {}) or {}
                        slot_key = f"{pos}_slot{slot}"
                        slot_rng = by_slot.get(slot_key) or {}
                        lst = None
                        if akey:
                            lst = (slot_rng.get("by_action", {}) or {}).get(akey) or ((slot_rng.get("range", {}) or {}).get("by_action", {}) or {}).get(akey)
                            if not lst:
                                lst = by_action_top.get(akey)
                        if not lst and akey == "RFI":
                            raw = slot_rng.get("range") or pos_map.get("range")
                            if isinstance(raw, dict):
                                raw = raw.get("by_action", {}).get(akey) or raw.get("by_action", {}).get("RFI")
                            if isinstance(raw, (list, tuple, set)):
                                lst = sorted(list(set(raw)))
                        if lst:
                            preview = sorted(list(set(lst)))[:12]
                            addon = " — " + akey + ": [" + ", ".join(preview) + "]"
                    except Exception:
                        addon = ""
    
                    out.append(desc + addon)
        except Exception:
            return out
        return out
    def build_hh_text(self) -> str:
        lines = ["**Players and Stacks:**"]
        for pos in POSITIONS:
            stack = self.stack_edits[pos].text().strip() or "0"
            lines.append(f"- {pos}: Stack {stack} BB")

        hole = []
        for pos in POSITIONS:
            c1, c2 = self.card_edits[pos]
            t1, t2 = (c1.text() or "").strip(), (c2.text() or "").strip()
            if t1 or t2:
                hole.append(f"{pos}: [{t1.upper()} {t2.upper()}]")
        if hole:
            lines.append("\n**Hole Cards:**")
            lines += [f"- {h}" for h in hole]

        flop = " ".join([x.upper() for x in [self.flop1.text(), self.flop2.text(), self.flop3.text()] if (x or '').strip()])
        trn = (self.turn.text() or "").strip().upper()
        rvr = (self.river.text() or "").strip().upper()
        if flop or trn or rvr:
            lines.append("\n**Board:**")
            if flop:
                lines.append(f"- Flop: [{flop}]")
            if trn:
                lines.append(f"- Turn: [{trn}]")
            if rvr:
                lines.append(f"- River: [{rvr}]")
        def block(title, body_lines):
            body_lines = [ln for ln in (body_lines or []) if ln.strip()]
            if not body_lines: return ""
            body = "\n".join([f"- {ln}" for ln in body_lines])
            return f"\n\n**{title} Actions:**\n{body}"

        out = "\n".join(lines)
        out += block("Preflop", self._preflop_lines_with_ranges())
        out += block("Flop", self.flop_form.to_lines())
        out += block("Turn", self.turn_form.to_lines())
        out += block("River", self.river_form.to_lines())
        return out

    def build_struct(self) -> dict:
        stacks = {pos: float((self.stack_edits[pos].text() or "0").replace(",",".")) for pos in POSITIONS}
        hole = {}
        for pos in POSITIONS:
            c1, c2 = self.card_edits[pos]
            t1, t2 = (c1.text() or "").strip().upper(), (c2.text() or "").strip().upper()
            if t1 or t2:
                hole[pos] = [t1, t2]
        board = {
            "flop": [x.strip().upper() for x in [self.flop1.text(), self.flop2.text(), self.flop3.text()] if (x or "").strip()],
            "turn": (self.turn.text() or "").strip().upper(),
            "river": (self.river.text() or "").strip().upper(),
        }
        def _collect(street_form):
            out = []
            for pos in POSITIONS:
                cb, sz = street_form.rows[pos]
                act = cb.currentText()
                size = (sz.text() or "").strip().replace(",", ".")
                if act and act != "—":
                    item = {"pos": pos, "action": act}
                    if act in ("bets","raises","calls","all-in","opens") and size:
                        try:
                            item["size_bb"] = float(size)
                        except Exception:
                            item["size_bb"] = size
                    out.append(item)
            return out
        actions = {
            "preflop": _collect(self.pre_form),
            "flop": _collect(self.flop_form),
            "turn": _collect(self.turn_form),
            "river": _collect(self.river_form),
        }
        # include ranges (per-slot) for persistence between dialog opens
        ranges = getattr(self, 'ranges', {}) or {}
        return {
            "stacks": stacks,
            "hole_cards": hole,
            "board": board,
            "actions": actions,
            "ranges": ranges,
        }
    
    def _on_flop1_edited(self):
        try:
            text = self.flop1.text()
            cards = self._parse_three_cards(text)
            if cards:
                self.flop1.setText(self._fmt_card_ui(cards[0]))
                self.flop2.setText(self._fmt_card_ui(cards[1]))
                self.flop3.setText(self._fmt_card_ui(cards[2]))
        except Exception:
            pass

    def pick_flop_triple(self):
        try:
            used = self._collect_used_cards(exclude_edits=[self.flop1, self.flop2, self.flop3])
            dlg = FlopPicker(self, used_cards=used)
            if dlg.exec():
                cards = dlg.selected
                if isinstance(cards, (list, tuple)) and len(cards) == 3:
                    self.flop1.setText(self._fmt_card_ui(cards[0]))
                    self.flop2.setText(self._fmt_card_ui(cards[1]))
                    self.flop3.setText(self._fmt_card_ui(cards[2]))
        except Exception:
            pass

    def showEvent(self, ev):
        try:
            self._dock_right_of_parent()
        except Exception:
            pass
        super().showEvent(ev)
    def pick_hole_cards(self, pos):

        try:
            c1, c2 = self.card_edits.get(pos, (None, None))
            used = self._collect_used_cards(exclude_edits=[c1, c2])
            dlg = CardPicker(self, pick_two=True, used_cards=used)
            if dlg.exec():
                cards = dlg.selected or []
                if isinstance(cards, (list, tuple)) and len(cards) >= 2:
                    c1, c2 = self.card_edits.get(pos, (None,None))
                    if c1: c1.setText(str(cards[0]))
                    if c2: c2.setText(str(cards[1]))
        except Exception as e:
            pass

    def eventFilter(self, obj, ev):
        try:
            from PyQt6.QtCore import QEvent
            if ev.type() in (QEvent.Type.Move, QEvent.Type.Resize):
                self._dock_right_of_parent()
        except Exception:
            pass
        return super().eventFilter(obj, ev)

    def _update_range_label(self, pos):
        try:
            data = self.ranges.get(pos)
            n = 0
            if isinstance(data, dict):
                union = set()
                by_slot = data.get('by_slot', {}) or {}
                for slot_data in by_slot.values():
                    rng = slot_data.get('range')
                    union |= _flatten_slot_union(rng)
                # legacy per-action container
                if not union and 'by_action' in data:
                    for v in (data.get('by_action') or {}).values():
                        union.update(v or [])
                n = len(union)
            elif isinstance(data, (list, set, tuple)):
                n = len(data)
            self.range_labels[pos].setText(f"{n} hand")
        except Exception:
            pass

    def pick_range(self, pos):
        try:
            initial = self.ranges.get(pos) or []
            dlg = RangeSelectorDialog(self, initial=initial, title=f"{pos} – Range kiválasztó"); dlg.resize(560, 560)
            if dlg.exec():
                # Prefer the teljes (minden akció + frekvencia) eredmény, visszafelé kompatibilis fallbackkel
                self.ranges[pos] = getattr(dlg, 'result_all', None) or dlg.selected
                self._update_range_label(pos)
        except Exception:
            pass

    def pick_range_for_action(self, pos, action_name):
        """
        Store ranges independently per R-button (slot), not just by action name.
        Backwards compatible: existing data['by_action'] left untouched.
        """
        try:
            # unique key from the clicked button, so each "R" is independent
            btn = getattr(self, 'sender', lambda: None)()
            slot_key = None
            if btn is not None:
                try:
                    idx = btn.property("slot_index")
                    if idx is not None:
                        slot_key = f"{pos}_slot{int(idx)}"
                except Exception:
                    slot_key = None
            # fallback: include action name to avoid collisions if sender() fails
            if not slot_key:
                slot_key = f"{pos}_slot0"
            data = self.ranges.get(pos)
            if not isinstance(data, dict):
                data = {"by_slot": {}}
            by_slot = data.get("by_slot", {})
            slot_entry = by_slot.get(slot_key, {})
            initial = slot_entry.get("range", [])
            dlg = RangeSelectorDialog(self, initial=initial, title=f"{pos} – {action_name} range")
            dlg.resize(560, 560)
            if dlg.exec():
                res = getattr(dlg, "result_all", None) or getattr(dlg, "selected", [])
                by_slot[slot_key] = {"action": action_name, "range": res}
                data["by_slot"] = by_slot
                self.ranges[pos] = data
                self._update_range_label(pos)
        except Exception:
            pass


# --- Auto-added: build {"<pos> <action>": [hands...] } from the Manual Entry UI ---

def _assigned_ranges_for_hh(self):
    """
    Build {"<POS> <action>": [hands...]} from the Manual Entry dialog state.

    - Uses StreetForm (preflop) combo values per slot
    - Reads ranges from self.ranges[pos]["by_slot"][f"{pos}_slot{idx}"]
      (falls back to by_action or plain list)
    - Flattens dict results (result_all) into a simple hand list
    """
    try:
        POS = POSITIONS if "POSITIONS" in globals() else ["UTG","HJ","CO","BTN","SB","BB"]
        rows_obj = getattr(self, "pre_form", None)
        rows = getattr(rows_obj, "rows", {}) if rows_obj is not None else {}
        assigned = {}

        def _flatten(v):
            try:
                return _flatten_slot_union(v)
            except Exception:
                # list-like or None
                if isinstance(v, (list,tuple,set)):
                    return list(v)
                return []

        for pos in POS:
            pair_list = rows.get(pos, []) or []
            data = (getattr(self, "ranges", {}) or {}).get(pos, {}) or {}
            by_slot = data.get("by_slot", {}) if isinstance(data, dict) else {}
            by_action = data.get("by_action", {}) if isinstance(data, dict) else {}

            for idx, pair in enumerate(pair_list):
                try:
                    cb, sz = pair
                except Exception:
                    continue
                act = (cb.currentText() or "").strip().lower()
                if not act or act == "—":
                    continue
                key = f"{pos} {act}"
                slot_key = f"{pos}_slot{idx}"
                entry = by_slot.get(slot_key, {}) if isinstance(by_slot, dict) else {}
                rng = entry.get("range")
                if not rng:
                    rng = by_action.get(act) or data
                hands = _flatten(rng)
                assigned[key] = hands
        return assigned
    except Exception:
        return {}

