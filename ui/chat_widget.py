
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QHBoxLayout

# --- Robust import for coach_reply -------------------------------------------------
try:
    from ai_coach.kkpoker_ai.coach import coach_reply  # type: ignore
except Exception:
    try:
        from kkpoker_ai.coach import coach_reply  # type: ignore
    except Exception:
        import sys, os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from kkpoker_ai.coach import coach_reply  # type: ignore

class ChatWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parsed_context = None

        lay = QVBoxLayout(self)
        self.header = QLabel("AI Coach — a kontextus itt jelenik meg a HH feldolgozása után.")
        from PyQt6.QtWidgets import QSizePolicy
        self.header.setWordWrap(True)
        self.header.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.header.setMaximumHeight(16777215)  # allow full expansion
        lay.addWidget(self.header)

        self.chat_log = QTextEdit(self)
        self.chat_log.setReadOnly(True)
        lay.addWidget(self.chat_log, 3)

        self.input = QTextEdit(self)
        self.input.setPlaceholderText("Írj egy kérdést (pl. 'BTN nyit 2.5x vs SB 3bet?')")
        lay.addWidget(self.input, 1)

        self.btn = QPushButton("Send to Coach")
        self.btn.clicked.connect(self.handle_send)
        lay.addWidget(self.btn)

    # Kapcsolat a Replayerrel: kézhez kapjuk a feldolgozott handet
    def onParsedHand(self, out: dict):
        self.parsed_context = out or {}
        # rövid összefoglaló a fejlécbe
        pls = self.parsed_context.get("players", {})
        acts = self.parsed_context.get("actions", [])
        players_txt = ", ".join([f"{p}: {pls[p].get('stack',0)}BB" for p in ["UTG","HJ","CO","BTN","SB","BB"] if p in pls])
        acts_txt = "; ".join([f"{a.get('street','')}/{a.get('pos','')}/{a.get('move','')}" for a in acts[:6]])
        self.header.setText(f"AI Coach kontextus\nJátékosok: {players_txt}\nAkciók: {acts_txt}")

    def handle_send(self):
        msg = self.input.toPlainText().strip()
        if not msg:
            return
        self.chat_log.append(f"TE: {msg}")
        try:
            reply = coach_reply(self.parsed_context, msg)
        except Exception as e:
            reply = f"[HIBA] {e}"
        self.chat_log.append(f"EDZŐ: {reply}\n")
        self.input.clear()
