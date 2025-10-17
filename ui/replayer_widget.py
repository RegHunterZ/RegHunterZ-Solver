from ai_coach.inline_range_hh import inject_ranges_into_hh

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QGroupBox, QHBoxLayout,
    QComboBox, QSplitter, QSizePolicy, QVBoxLayout as QVBL
)

# --- Robust imports for hh_parser (package or script) ---
try:
    from ai_coach.kkpoker_ai.hh_parser import parse_hh, ensure_sixmax  # type: ignore
except Exception:
    try:
        from kkpoker_ai.hh_parser import parse_hh, ensure_sixmax  # type: ignore
    except Exception:
        import sys, os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from kkpoker_ai.hh_parser import parse_hh, ensure_sixmax  # type: ignore

from .manual_entry import ManualEntryDialog
from .replay_view import ReplayView
from .visual_replayer import VisualReplayer

class ReplayerWidget(QWidget):
    onParsed = pyqtSignal(dict)


    
    
    
    def _apply_blinds(self, state: dict, sb_size: float = 0.5, bb_size: float = 1.0):
        """Ensure SB/BB post actions are present once. Does NOT mutate stacks or pot."""
        try:
            if state.get("_blinds_applied"):
                return state
            players = state.get("players", {}) or {}
            actions = list(state.get("actions", []) or [])
            mv_text = " | ".join([f"{a.get('pos','')} {a.get('action', a.get('move',''))}".lower() for a in actions[:8]])
            has_sb_post = ("sb post" in mv_text)
            has_bb_post = ("bb post" in mv_text)
            if not (has_sb_post and has_bb_post):
                blind_actions = [
                    {"street":"Preflop","pos":"SB","move":"SB post","size": float(sb_size)},
                    {"street":"Preflop","pos":"BB","move":"BB post","size": float(bb_size)},
                ]
                state["actions"] = blind_actions + actions
            else:
                state["actions"] = actions
            state["_blinds_applied"] = True
            state["players"] = players
            return state
        except Exception:
            return state

    def __init__(self):
        super().__init__()
        self._manual_dlg = None  # keep dialog state

        root = QHBoxLayout(self)
        root.setContentsMargins(6,6,6,6)
        root.setSpacing(6)

        # Splitter: left (HH + controls + tables) | right (Replay)
        split = QSplitter(self)
        split.setOrientation(Qt.Orientation.Horizontal)
        root.addWidget(split)

        # Left column
        left = QWidget()
        left_v = QVBoxLayout(left); left_v.setContentsMargins(0,0,0,0); left_v.setSpacing(6)

        # HH text
        hh_box = QGroupBox("HH szöveg")
        hh_lay = QVBoxLayout(hh_box)
        hh_lay.addWidget(QLabel("Illeszd be a HH-t, vagy használd a Manuális bevitelt:"))
        self.hh_edit = QTextEdit(self)
        self.hh_edit.setPlaceholderText("Ide illeszd a KKPoker HH szöveget...")
        hh_lay.addWidget(self.hh_edit)
        left_v.addWidget(hh_box, 4)

        # Actions
        actions_box = QGroupBox("Műveletek")
        ab = QHBoxLayout(actions_box)
        # mode selector removed per user request
        self.btn_manual = QPushButton("Manuális bevitel")
        self.btn_manual.clicked.connect(self.handle_manual_entry)
        self.btn_parse = QPushButton("Feldolgozás"); self.btn_parse.clicked.connect(self.handle_parse)
        ab.addStretch(1); ab.addWidget(self.btn_manual); ab.addWidget(self.btn_parse); ab.addStretch(1)
        left_v.addWidget(actions_box)

        # Summary tables
        bottom_box = QGroupBox("Feldolgozott összegzés")
        # Hide the summary panel per user request (kept for internal state only)
        try:
            bottom_box.setVisible(False)
            bottom_box.setFixedHeight(0)
            bottom_box.setMaximumHeight(0)
        except Exception:
            pass
        v = QVBoxLayout(bottom_box)
        self.players_tbl = QTableWidget(0,3); self.players_tbl.setHorizontalHeaderLabels(["Pozíció","Név","Stack (BB)"]); self.players_tbl.verticalHeader().setVisible(False); self.players_tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        v.addWidget(self.players_tbl)
        self.actions_tbl = QTableWidget(0,3); self.actions_tbl.setHorizontalHeaderLabels(["Street","Pozíció","Akció + Méret"]); self.actions_tbl.verticalHeader().setVisible(False); self.actions_tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        v.addWidget(self.actions_tbl)
        # left_v.addWidget(bottom_box, 3)  # removed per user request

        split.addWidget(left)

        # Right column: Replay
        right = QWidget(); right_v = QVBoxLayout(right); right_v.setContentsMargins(0,0,0,0)
        self.replay_box = QGroupBox(""); self.replay_box.setFlat(True); rb_l = QVBL(self.replay_box)
        self.visual_replayer = VisualReplayer(self); rb_l.addWidget(self.visual_replayer, 3)
        self.replay = ReplayView(self)
        # Show only the control bar: table hidden inside replay_view.py
        try:
            self.replay.setVisible(True)
            self.replay.setMinimumHeight(64)
            self.replay.setMaximumHeight(96)
        except Exception:
            pass
        rb_l.addWidget(self.replay, 0)
        try:
            self.replay.stepChanged.connect(self.visual_replayer.set_step)
        except Exception:
            pass
        # Emphasize visual replayer area
        try:
            rb_l.setStretch(0, 9)
        except Exception:
            pass
        right_v.addWidget(self.replay_box)
        split.addWidget(right)

        split.setSizes([520, 980])
        self.replay_box.setMinimumSize(520, 420)

    def handle_manual_entry(self):
        if self._manual_dlg is None:
            self._manual_dlg = ManualEntryDialog(self)
        dlg = self._manual_dlg
        # ha korábbi manuális struktúra van, töltsük vissza, hogy szerkeszthető legyen
        try:
            if hasattr(self, '_manual_struct') and self._manual_struct:
                dlg.load_struct(self._manual_struct)
        except Exception:
            pass
        if dlg.exec():
            hh = dlg.build_hh_text()
            self.hh_edit.setPlainText(inject_ranges_into_hh(hh, getattr(dlg, '_assigned_ranges_for_hh', lambda: {})()))
            # store structured manual data for processing
            try:
                self._manual_struct = dlg.build_struct()
            except Exception:
                self._manual_struct = None
            self.handle_parse()

    
    
    
    def handle_parse(self):
        # prefer structured manual data if available
        if hasattr(self, "_manual_struct") and self._manual_struct:
            ms = self._manual_struct
            # players
            players = {pos: {"name": "", "stack": ms.get("stacks", {}).get(pos, 0)} for pos in ["UTG","HJ","CO","BTN","SB","BB"]}
            # actions: normalize to existing schema
            actions = []
            order = [("Preflop","preflop"),("Flop","flop"),("Turn","turn"),("River","river")]
            for street_label, key in order:
                for a in ms.get("actions", {}).get(key, []):
                    mv = a.get("action", "")
                    if mv == "post":
                        mv = f"{a.get('pos','')} post"
                    actions.append({"street": street_label, "pos": a.get("pos",""), "move": mv, "size": a.get("size_bb")})
            # hole cards attach
            hc = ms.get("hole_cards", {}) or {}
            for pos, cards in hc.items():
                if pos in players:
                    players[pos]["cards"] = cards
            out = {"players": players, "actions": actions}

            # --- Inject street markers for board-only streets (so VisualReplayer can advance streets) ---
            try:
                b = ms.get("board", {}) or {}
                def _has(v): 
                    if isinstance(v, (list,tuple)): 
                        return len([x for x in v if x]) > 0
                    return bool(v)
                markers = []
                if _has(b.get("flop")):
                    markers.append({"street": "Flop", "pos": "", "move": "—", "size": None})
                if _has(b.get("turn")):
                    markers.append({"street": "Turn", "pos": "", "move": "—", "size": None})
                if _has(b.get("river")):
                    markers.append({"street": "River", "pos": "", "move": "—", "size": None})
                def _has_street(label):
                    return any(a.get("street")==label for a in actions)
                if markers:
                    if not _has_street("Flop"): actions = [m for m in markers if m.get("street")=="Flop"] + actions
                    if not _has_street("Turn"): actions = [m for m in markers if m.get("street")=="Turn"] + actions
                    if not _has_street("River"): actions = [m for m in markers if m.get("street")=="River"] + actions
            except Exception:
                pass
            # --- end markers ---
            # apply auto blinds once
            out = self._apply_blinds(out)
            # update replayers
            self.replay.set_state(out.get("players", {}), out.get("actions", []))
            try:
                b = ms.get("board", {})
                self.visual_replayer.load_from_manual({"players": out.get("players", {}), "actions": out.get("actions", []), "board": b})
            except Exception:
                self.visual_replayer.set_state(out.get("players", {}), out.get("actions", []))
            self.onParsed.emit(out)
            return

        # Non-manual (HH text) path
        text = self.hh_edit.toPlainText()
        ph = parse_hh(text)
        out = {
            "players": {p.pos: {"name": p.name, "stack": p.stack} for p in ph.players.values()},
            "actions": [{"street": a.street, "pos": a.pos, "move": a.move, "size": a.size} for a in ph.actions]
        }
        out = ensure_sixmax(text, out)
        out = self._apply_blinds(out)
        self.replay.set_state(out.get("players", {}), out.get("actions", []))
        self.visual_replayer.set_state(out.get("players", {}), out.get("actions", []))
        self.onParsed.emit(out)

# --- Auto-added helper for HH inline ranges ---

# Auto-wiring helper: safely builds the {"UTG bets": [...], ...} dict from UI state.
# Expected to be mixed into the ManualEntryDialog (or similar).
def _assigned_ranges_for_hh(self):
    # Best-effort: if you already maintain self.ranges as {action_key: [hands...]}, we forward it.
    # Accepts either hand-codes or (row,col) pairs; the inject function tolerates empty dict.
    try:
        from inline_range_hh.range_util import flatten_selected_cells
    except Exception:
        flatten_selected_cells = None

    r = {}
    src = getattr(self, "ranges", {}) or getattr(self, "action_ranges", {}) or {}
    # try to detect structure
    for key, val in src.items():
        # key should look like "UTG bets", "BB raises", "UTG calls", etc.
        if not isinstance(key, str):
            continue
        hands = []
        if not val:
            r[key] = hands
            continue
        # If hand-codes already:
        if all(isinstance(x, str) and len(x) in (2,3) for x in val):
            hands = list(val)
        # If (row,col) tuples from 13x13:
        elif flatten_selected_cells and all(isinstance(x, (list,tuple)) and len(x)==2 for x in val):
            hands = flatten_selected_cells(val)
        r[key] = hands
    return r
