import re
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPixmap
from PyQt6.QtCore import Qt, QRectF, QPointF
import os, math

SEATS = ["UTG","HJ","CO","BTN","SB","BB"]
ASSETS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
CARDS = os.path.join(ASSETS, "cards_kk")
LOGO = os.path.join(ASSETS, "logo.png")

class VisualReplayer(QWidget):
    def _card_pix(self, code: str):
        try:
            if not hasattr(self, "_card_cache"):
                self._card_cache = {}
            code = (code or "").strip()
            if len(code) < 2:
                return QPixmap()
            r = code[0].upper()
            s = code[1].lower()
            key = r+s
            if key in self._card_cache:
                return self._card_cache[key]
            path = os.path.join(CARDS, f"{key}.png")
            pm = QPixmap(path) if os.path.exists(path) else QPixmap()
            self._card_cache[key] = pm
            return pm
        except Exception:
            return QPixmap()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.players = {}
        self.actions = []
        self.step = -1
        self._logo = QPixmap(LOGO) if os.path.exists(LOGO) else QPixmap()

    
    def _norm_card(self, s):
        if not s: 
            return ''
        s = str(s).upper()
        # remove brackets/commas/spaces
        s = re.sub(r'[^A-Z0-9]', '', s)
        # map 10 to T
        s = s.replace('10','T')
        # allow formats like 'AH' 'AS' or 'A♥' etc already stripped to AH
        # ensure length 2
        if len(s) >= 2:
            # take last char as suit if in H D C S, else try first 2 meaningful
            suit_chars = 'HDCS'
            # find first suit char from right
            suit = ''
            for ch in reversed(s):
                if ch in suit_chars:
                    suit = ch
                    break
            # find rank (A K Q J T 9..2)
            ranks = 'AKQJT98765432'
            rank = ''
            for ch in s:
                if ch in ranks:
                    rank = ch
                    break
            if rank and suit:
                return rank + suit
        return s[:2]

    def _normalize_board(self, b):
        # returns dict with flop(list), turn(str), river(str)
        out = {'flop': [], 'turn': '', 'river': ''}
        if not b:
            return out
        flop = b.get('flop') if isinstance(b, dict) else b
        turn = b.get('turn','') if isinstance(b, dict) else ''
        river = b.get('river','') if isinstance(b, dict) else ''
        # flop can be list or string
        if isinstance(flop, str):
            # split on non-alnum
            parts = re.split(r'[^A-Za-z0-9]+', flop)
            parts = [p for p in parts if p]
        elif isinstance(flop, (list,tuple)):
            parts = list(flop)
        else:
            parts = []
        parts = [self._norm_card(p) for p in parts][:3]
        out['flop'] = [p for p in parts if p]
        out['turn'] = self._norm_card(turn) if isinstance(turn, str) or turn else ''
        out['river'] = self._norm_card(river) if isinstance(river, str) or river else ''
        return out

    def load_from_manual(self, data: dict):
        try:
            b = data.get('board')
            self.board = self._normalize_board(b) if hasattr(self, '_normalize_board') else b
        except Exception:
            self.board = {'flop': [], 'turn': '', 'river': ''}
        self.set_state(data.get('players', {}), data.get('actions', []))
        try:
            self.update(); self.repaint()
        except Exception:
            pass
        try:
            self.update()
        except Exception:
            pass

    def set_state(self, players, actions):
        self.players = players or {}
        self.actions = actions or []
        self.step = -1
        self.update()

    def set_step(self, i:int):
        self.step = i
        self.update()

    def _seat_positions(self, rect):
        cx, cy = rect.center().x(), rect.center().y()
        rx, ry = rect.width()*0.45, rect.height()*0.35
        coords = {}
        for idx, pos in enumerate(SEATS):
            ang = 2*math.pi*idx/6.0 - math.pi/2
            x = cx + rx*math.cos(ang)
            y = cy + ry*math.sin(ang)
            coords[pos] = QPointF(x,y)
        return coords

    def _draw_table(self, p: QPainter, rect):
        p.fillRect(rect, QColor(28,43,58))  # app theme bg

        # center logo (background, under chips/cards)
        if not self._logo.isNull():
            L = int(min(rect.width(), rect.height()) * 0.55)
            pm = self._logo.scaled(L, L, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            p.setOpacity(0.22)
            p.drawPixmap(int(rect.center().x() - pm.width()/2), int(rect.center().y() - pm.height()/2), pm)
            p.setOpacity(1.0)

    def _current_street(self):
        try:
            # Determine street from actions up to current step
            streets = [a.get('street','Preflop') for a in (self.actions or [])]
            if self.step is None or self.step < 0:
                return 'Preflop'
            upto = streets[:self.step+1]
            # Last seen street label
            for s in reversed(upto):
                if s in ('Preflop','Flop','Turn','River'):
                    return s
            return 'Preflop'
        except Exception:
            return 'Preflop'

    def _pot_until_step(self, upto: int) -> float:
        pot = 0.0
        if not isinstance(self.actions, list) or len(self.actions) == 0:
            return 0.0
        try:
            upto = int(upto)
        except Exception:
            upto = 0
        upto = max(0, min(upto, len(self.actions)-1))
        for k in range(upto+1):
            a = self.actions[k] or {}
            mv = str(a.get("move", a.get("action",""))).lower()
            try: sz = float(a.get("size") or a.get("size_bb") or 0.0)
            except Exception: sz = 0.0
            if (('post' in mv) or (mv in ('ante','straddle','bets','raises','opens','all-in','calls'))):
                pot += max(0.0, sz)
        return pot

    def _stack_after(self, pos: str, step: int) -> float:
        try:
            pos = str(pos).upper()
            base = float((self.players.get(pos, {}) or {}).get("stack", 0.0))
            if not isinstance(self.actions, list): 
                return base
            try: step = int(step)
            except Exception: step = 0
            step = max(step, 0)
            limit = max(0, min(step, len(self.actions)-1))
            for i in range(limit+1):
                a = self.actions[i] or {}
                mv = str(a.get('move', a.get('action',''))).lower()
                ap = str(a.get('pos','')).upper()
                try: sz = float(a.get('size') or a.get('size_bb') or 0.0)
                except Exception: sz = 0.0
                if ap == pos and any(k in mv for k in ['post','bet','raise','call','ante','straddle']):
                    base -= max(0.0, sz)
            return max(0.0, base)
        except Exception:
            return float((self.players.get(pos, {}) or {}).get("stack", 0.0))

    def _draw_board_cards(self, p: QPainter, rect: QRectF):
        # Determine current street and choose how many cards to show
        try:
            street = self._current_street()
        except Exception:
            street = 'Preflop'
        b = getattr(self, 'board', {'flop': [], 'turn': '', 'river': ''}) or {'flop': [], 'turn': '', 'river': ''}
        flop = list(b.get('flop') or [])[:3]
        turn = b.get('turn') or ''
        river = b.get('river') or ''

        show = 0
        if street == 'Flop':
            show = min(3, len(flop))
        elif street == 'Turn':
            show = min(4, len(flop) + (1 if turn else 0))
        elif street == 'River':
            show = min(5, len(flop) + (1 if turn else 0) + (1 if river else 0))
        else:
            show = 0

        cards = []
        if show >= 1 and len(flop) >= 1: cards.append(flop[0])
        if show >= 2 and len(flop) >= 2: cards.append(flop[1])
        if show >= 3 and len(flop) >= 3: cards.append(flop[2])
        if show >= 4 and turn: cards.append(turn)
        if show >= 5 and river: cards.append(river)
        if not cards:
            return

        # Layout just under the POT label, at center
        total = len(cards)
        gap = 10.0
        cw, ch = 44.0, 62.0
        width = total*cw + (total-1)*gap
        x0 = rect.center().x() - width/2.0
        y0 = rect.center().y() + 20.0

        font = QFont(self.font())
        font.setPointSize(11)

        for i, code in enumerate(cards):
            pm = None
            try:
                pm = self._card_pix(code)
            except Exception:
                pm = None
            x = int(x0 + i*(cw+gap))
            y = int(y0)
            if pm and hasattr(pm, "isNull") and not pm.isNull():
                pmr = pm.scaled(int(cw), int(ch), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                p.drawPixmap(x, y, pmr)
            else:
                # Fallback: draw placeholder card with the text code
                r = QRectF(x, y, cw, ch)
                p.setPen(QPen(QColor(220,220,220)))
                p.setBrush(QBrush(QColor(30,30,30)))
                p.drawRoundedRect(r, 6, 6)
                p.setFont(font)
                p.drawText(r, int(Qt.AlignmentFlag.AlignCenter), str(code))


    
    def paintEvent(self, ev):
        p = QPainter(self)
        try:
            p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
            rect = self.rect()
            self._draw_table(p, rect)
            coords = self._seat_positions(rect)
            # seats + stacks
            for pos, pt in coords.items():
                box = QRectF(pt.x()-60, pt.y()-20, 120, 40)
                p.setBrush(QColor(30,30,30))
                p.setPen(QColor(220,220,220))
                p.drawRoundedRect(box, 10, 10)
                p.setPen(Qt.GlobalColor.white)
                p.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
                p.drawText(QRectF(box.x(), box.y()-2, box.width(), 24), Qt.AlignmentFlag.AlignCenter, pos)
                stack = self._stack_after(pos, self.step if isinstance(self.step,int) else 0)
                p.setFont(QFont("Segoe UI", 10))
                p.drawText(QRectF(box.x(), box.y()+18, box.width(), 20), Qt.AlignmentFlag.AlignCenter, f"{stack:.1f} bb")
                # hole cards below box
                cards = (self.players.get(pos, {}) or {}).get("cards", [])
                try:
                    c1, c2 = (cards[0], cards[1]) if isinstance(cards,(list,tuple)) and len(cards)>=2 else (None,None)
                except Exception:
                    c1, c2 = (None,None)
                if c1 and c2:
                    pm1 = self._card_pix(c1); pm2 = self._card_pix(c2)
                    if not pm1.isNull() and not pm2.isNull():
                        # 
                        # calc target size based on table size
                        ch = 42
                        try:
                            ch = max(28, int(self.height()*0.07))
                        except Exception:
                            pass
                        cw = int(ch * 3 / 4)
                        gap = 6
                        total_w = cw*2 + gap
                        x0 = box.center().x() - total_w/2
                        y0 = box.y() + box.height() + 6
                        pm1s = pm1.scaled(cw, ch, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        pm2s = pm2.scaled(cw, ch, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        p.drawPixmap(int(x0), int(y0), pm1s)
                        p.drawPixmap(int(x0 + cw + gap), int(y0), pm2s)
## DEALER_BUTTON
            # draw Dealer button next to BTN seat
            try:
                btn_pt = coords.get("BTN")
                if btn_pt is not None:
                    # place to the outside-right of BTN box
                    dbx = btn_pt.x() + 78
                    dby = btn_pt.y() - 22
                    d = 28.0
                    p.setBrush(QColor(255,255,255))
                    p.setPen(QPen(QColor(40,40,40), 2))
                    p.drawEllipse(QRectF(dbx, dby, d, d))
                    p.setPen(QColor(0,0,0))
                    p.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
                    p.drawText(QRectF(dbx, dby, d, d), Qt.AlignmentFlag.AlignCenter, "D")
            except Exception:
                pass

            # pot label
            p.setPen(QColor(255,255,180))
            p.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            step_val = self.step if isinstance(self.step, int) else 0
            pot = self._pot_until_step(step_val)
            p.drawText(QRectF(rect.center().x()-100, rect.center().y()-20, 200, 40),
                       Qt.AlignmentFlag.AlignCenter, f"POT: {pot:.1f} bb")
            self._draw_board_cards(p, QRectF(rect))
            # draw board cards under pot
            self._draw_board_cards(p, QRectF(rect))
            # chips
            if isinstance(self.actions, list) and len(self.actions) > 0 and isinstance(step_val, int):
                limit = max(0, min(step_val, len(self.actions)-1))
                for i in range(limit+1):
                    a = self.actions[i]
                    pos = a.get("pos"); mv = str(a.get("move",""))
                    if pos not in coords: continue
                    mv_l = mv.lower()
                    if not (('post' in mv_l) or (mv_l in ('bets','raises','opens','all-in','calls','ante','straddle'))): continue
                    pt = coords[pos]
                    cx, cy = rect.center().x(), rect.center().y()
                    px = pt.x() + (cx - pt.x())*0.35
                    py = pt.y() + (cy - pt.y())*0.35
                    ## CHIP_COLOR_BY_MOVE_ENH
                    mv = str(a.get('move','')).lower()
                    if 'sb' in mv and 'post' in mv:
                        p.setBrush(QColor(60,120,220))
                        p.setPen(QPen(QColor(30,60,120), 2))
                    elif 'bb' in mv and 'post' in mv:
                        p.setBrush(QColor(220,60,60))
                        p.setPen(QPen(QColor(120,30,30), 2))
                    elif mv.strip() == 'post':
                        pos = str(a.get('pos','')).upper()
                        if pos == 'SB':
                            p.setBrush(QColor(60,120,220)); p.setPen(QPen(QColor(30,60,120), 2))
                        elif pos == 'BB':
                            p.setBrush(QColor(220,60,60)); p.setPen(QPen(QColor(120,30,30), 2))
                        else:
                            p.setBrush(QColor(200,50,50))
                    else:
                        p.setBrush(QColor(200,50,50))
                        p.setPen(QPen(QColor(120,20,20), 2))
                    p.drawEllipse(QRectF(px-12, py-12, 24, 24))
                    p.setPen(Qt.GlobalColor.white)
                    p.setFont(QFont("Segoe UI", 10))
                    try: sz = float(a.get('size') or a.get('size_bb') or 0)
                    except Exception: sz = 0.0
                    p.drawText(QRectF(px-30, py+12, 60, 18), Qt.AlignmentFlag.AlignCenter, f"{sz:.1f}")
        finally:
            try: p.end()
            except Exception: pass
