import re

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# Patterns
SEAT_RE = re.compile(r"^(UTG|HJ|CO|BTN|SB|BB)\s*:\s*Stack\s*([0-9.]+)", re.I | re.M)
ACTION_LINE_RE = re.compile(r"^(Preflop|Flop|Turn|River):\s*(.*)$", re.I | re.M)
BET_RE = re.compile(r"(UTG|HJ|CO|BTN|SB|BB)\s*(checks|calls|bets|raises|all-in|folds|opens)(?:\s*to\s*([0-9.]+))?", re.I)

# Nickname patterns (heuristic, supports 'Nick (POS)' or 'POS: Nick ...' lines)
NICK_POS_RE = re.compile(r"([^\(\)\n\r]+?)\s*\(\s*(UTG|HJ|CO|BTN|SB|BB)\s*\)", re.I)
POS_NICK_RE = re.compile(r"^(UTG|HJ|CO|BTN|SB|BB)\s*:\s*([^\n\r:]+?)(?:\s+Stack|\s*$)", re.I | re.M)

POS_ORDER = ["UTG", "HJ", "CO", "BTN", "SB", "BB"]
# Bullet players like "- Nick: 18 BB (UTG)"
STACK_BULLET_RE = re.compile(r"^[\-\u2022]\s*([^\n\r:]+?)\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*BB\s*\(\s*(UTG|HJ|CO|BTN|SB|BB)\s*\)\s*$", re.I | re.M)

def _parse_name_pos_map(hh_text: str):
    """Build maps: pos->name and name->pos from Players and Stacks section."""
    pos2name = {}; name2pos = {}
    for m in STACK_BULLET_RE.finditer(hh_text or ""):
        name = m.group(1).strip()
        pos = m.group(3).upper().strip()
        pos2name[pos] = name
        name2pos[name.lower()] = pos
    # also accept "POS: Nick ..." format
    for m in POS_NICK_RE.finditer(hh_text or ""):
        pos = m.group(1).upper().strip()
        name = m.group(2).strip()
        pos2name[pos] = name
        name2pos[name.lower()] = pos
    return pos2name, name2pos

# Bullet action lines under "**Preflop Actions:**" etc.
SECTION_RE = re.compile(r"\*\*(Preflop|Flop|Turn|River)\s+Actions\:\*\*(.*?)(?=\n\s*\*\*|$)", re.I | re.S)
BULLET_LINE_RE = re.compile(r"^[\-\u2022]\s*(.+?)\s*$", re.M)

def _parse_bullet_actions(hh_text: str):
    actions = []
    pos2name, name2pos = _parse_name_pos_map(hh_text)
    for sec in SECTION_RE.finditer(hh_text or ""):
        street = sec.group(1).capitalize()
        body = sec.group(2)
        for bm in BULLET_LINE_RE.finditer(body):
            line = bm.group(1).strip()
            low = line.lower()
            # name at start until verb
            name = None
            for n in name2pos.keys():
                if low.startswith(n.lower() + " "):
                    name = n
                    break
            if not name:
                # sometimes name contains spaces; take token before verb
                name = line.split()[0]
            pos = name2pos.get(name.lower())
            if not pos:
                # if we couldn't map, skip
                continue
            # classify move + size
            size = None
            move = None
            # standard verbs
            if " checks" in low or low.endswith("checks"):
                move = "checks"
            elif " folds" in low or low.endswith("folds"):
                move = "folds"
            elif " raises to " in low or " raises " in low:
                move = "raises"
                m = re.search(r"raises(?:\s*to)?\s*([0-9]+(?:\.[0-9]+)?)\s*bb", low)
                if m: size = float(m.group(1))
            elif " bets " in low:
                move = "bets"
                m = re.search(r"bets\s*([0-9]+(?:\.[0-9]+)?)\s*bb", low)
                if m: size = float(m.group(1))
            elif " calls " in low:
                move = "calls"
                m = re.search(r"calls\s*([0-9]+(?:\.[0-9]+)?)\s*bb", low)
                if m: size = float(m.group(1))
            if "all" in low and "in" in low.replace("-", " "):
                move = "all-in"
                m = re.search(r"all\s*[\-\s]?in\s*([0-9]+(?:\.[0-9]+)?)\s*bb", low)
                if m: size = float(m.group(1))
            if move:
                actions.append({"street": street, "pos": pos, "move": move, "size": size})
    return actions


# Extra pattern: '- NickName: 18 BB (UTG)'
STACK_BULLET_RE = re.compile(r"^[\-\u2022]?\s*([^\n\r:]+?)\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*BB\s*\(\s*(UTG|HJ|CO|BTN|SB|BB)\s*\)", re.I | re.M)

@dataclass
class Player:
    pos: str
    stack: float
    name: str = ""

@dataclass
class Action:
    street: str
    pos: str
    move: str
    size: Optional[float] = None

@dataclass
class ParsedHand:
    players: Dict[str, Player] = field(default_factory=dict)
    actions: List[Action] = field(default_factory=list)

def _extract_names(hh_text: str) -> Dict[str, str]:
    names: Dict[str, str] = {}
    # Pattern: "Nick (POS)"
    for m in NICK_POS_RE.finditer(hh_text or ""):
        nick = m.group(1).strip()
        pos = m.group(2).upper()
        if pos not in names and nick:
            names[pos] = nick
    # Pattern: "POS: Nick ..."
    for m in POS_NICK_RE.finditer(hh_text or ""):
        pos = m.group(1).upper()
        nick = m.group(2).strip()
        if pos not in names and nick:
            names[pos] = nick
    return names

def parse_hh(hh_text: str) -> ParsedHand:
    ph = ParsedHand()
    if not hh_text:
        return ph
    names = _extract_names(hh_text)
    # Players by SEAT_RE
    for m in SEAT_RE.finditer(hh_text):
        pos, stack = m.group(1).upper(), float(m.group(2))
        ph.players[pos] = Player(pos=pos, stack=stack, name=names.get(pos, ""))
    # Players by bullet
    for m in STACK_BULLET_RE.finditer(hh_text):
        name, stack_s, pos = m.group(1).strip(), m.group(2), m.group(3).upper()
        try: stack = float(stack_s)
        except: stack = 0.0
        ph.players[pos] = Player(pos=pos, stack=stack, name=name)
    # Actions: prefer bullet parsing
    acts = _parse_bullet_actions(hh_text)
    if acts:
        for a in acts:
            ph.actions.append(Action(street=a["street"], pos=a["pos"], move=a["move"], size=a["size"]))
    else:
        # fallback to compact "Street: ..." lines
        for m in ACTION_LINE_RE.finditer(hh_text):
            street = m.group(1).capitalize()
            tail = m.group(2)
            for a in BET_RE.finditer(tail):
                pos, move, size = a.group(1).upper(), a.group(2).lower(), a.group(3)
                ph.actions.append(Action(street=street, pos=pos, move=move, size=float(size) if size else None))
    return ph
    names = _extract_names(hh_text)
    try:
        for m in SEAT_RE.finditer(hh_text):
            pos, stack = m.group(1).upper(), float(m.group(2))
            ph.players[pos] = Player(pos=pos, stack=stack, name=names.get(pos, ""))
        for m in ACTION_LINE_RE.finditer(hh_text):
            street = m.group(1).capitalize()
            tail = m.group(2)
            for a in BET_RE.finditer(tail):
                pos, move, size = a.group(1).upper(), a.group(2).lower(), a.group(3)
                ph.actions.append(Action(street=street, pos=pos, move=move, size=float(size) if size else None))
    except Exception:
        pass
    return ph





def ensure_sixmax(hh_text: str, parsed: Dict) -> Dict:
    out = {"players": {}, "actions": []}
    out["actions"] = parsed.get("actions", [])
    names = _extract_names(hh_text)

    # 1) Inicializálás parsed alapján
    for k, v in parsed.get("players", {}).items():
        pos = (v.get("pos") if isinstance(v, dict) else getattr(v, "pos", k)) or k
        pos = str(pos).upper()
        stack = float((v.get("stack") if isinstance(v, dict) else getattr(v, "stack", 0)) or 0)
        name = (v.get("name") if isinstance(v, dict) else getattr(v, "name", "")) or names.get(pos, "")
        out["players"][pos] = {"pos": pos, "stack": stack, "name": name}

    # 2) SEAT_RE
    for m in SEAT_RE.finditer(hh_text or ""):
        pos, stack = m.group(1).upper(), float(m.group(2))
        cur = out["players"].get(pos, {})
        out["players"][pos] = {"pos": pos, "stack": stack, "name": cur.get("name", names.get(pos, ""))}

    # 3) BULLET (preflop)
    for m in STACK_BULLET_RE.finditer(hh_text or ""):
        name, stack_s, pos = m.group(1).strip(), m.group(2), m.group(3).upper()
        try:
            stack = float(stack_s)
        except Exception:
            continue
        out["players"][pos] = {"pos": pos, "stack": stack, "name": name or names.get(pos, out.get("players",{}).get(pos,{}).get("name",""))}

    # 4) Nettó költés visszaszámolás + felülírás all-in for less esetén
    try:
        spent, allin_flag, short_flag = _compute_spent(out["actions"])
        for pos, total in (spent or {}).items():
            if not total: 
                continue
            cur = out["players"].get(pos, {"pos": pos, "name": names.get(pos, "")})
            cur_stack = float(cur.get("stack", 0) or 0)
            if allin_flag.get(pos) or short_flag.get(pos):
                # Kötelező felülírás
                cur["stack"] = float(total)
                out["players"][pos] = cur
            else:
                # Heurisztika OCR-default ellen
                if cur_stack in (0.0, 100.0) or (cur_stack >= 35.0 and total <= 30.0):
                    cur["stack"] = float(total)
                    out["players"][pos] = cur
    except Exception:
        pass

    # 5) Helykitöltők + sorrend
    for pos in POS_ORDER:
        if pos not in out["players"]:
            out["players"][pos] = {"pos": pos, "stack": 0.0, "name": names.get(pos, "")}
    out["players"] = {pos: out["players"][pos] for pos in POS_ORDER}

    # --- RegHunterZ custom tweak: force blinds and default stacks ---
    # Default missing stacks to 100bb
    for pos, pdata in out["players"].items():
        try:
            if float(pdata.get("stack") or 0.0) <= 0.0:
                pdata["stack"] = 100.0
        except Exception:
            pdata["stack"] = 100.0

    # Check if Preflop contains explicit blind posts
    def _has_post(pos):
        for a in out.get("actions", []):
            st = str(a.get("street","")).lower()
            if st.startswith("pre") and a.get("pos") == pos and str(a.get("move","")).lower() in ("post","posts","puts"):
                return True
        return False

    forced = []
    if not _has_post("SB"):
        out["actions"] = [{"street":"Preflop","pos":"SB","move":"post","size":0.5}] + out["actions"]
        forced.append(("SB", 0.5))
    if not _has_post("BB"):
        out["actions"] = [{"street":"Preflop","pos":"BB","move":"post","size":1.0}] + out["actions"]
        forced.append(("BB", 1.0))

        return out






def _compute_spent(actions_list):
    """
    Heurisztikus költés-számítás utcánként.
    Visszaad: (spent_per_pos, allin_flag_per_pos, short_call_flag_per_pos)
    short_call_flag: igaz, ha a játékos megadása < szükséges kiegészítés (all-in for less).
    """
    spent = {}
    allin_flag = {}
    short_flag = {}
    put = {}
    max_put = 0.0
    cur_street = None

    for a in actions_list:
        street = a.get("street","")
        if street != cur_street:
            cur_street = street
            put = {}
            max_put = 0.0

        pos = (a.get("pos","") or "").upper()
        move = (a.get("move","") or "").lower()
        size = a.get("size", None)
        size = float(size) if size not in (None, "") else None

        spent.setdefault(pos, 0.0)
        put.setdefault(pos, 0.0)
        allin_flag.setdefault(pos, False)
        short_flag.setdefault(pos, False)

        if move in ("checks","folds",""):
            continue
        elif move in ("bets","opens"):
            if size is None: continue
            delta = max(0.0, size)
            put[pos] = max(put[pos], delta)
            spent[pos] += delta
            max_put = max(max_put, put[pos])
        elif move == "calls":
            if max_put == 0.0:
                # limp jelleg
                delta = max(0.0, size or 0.0)
            else:
                # szükséges kiegészítés
                needed = max(0.0, max_put - put[pos])
                if size is not None and size <= needed + 1e-6:
                    # ha méretet ad a UI, úgy kezeljük mint nettó megadás
                    delta = max(0.0, size)
                    # ha jóval kisebb, mint a szükséges kiegészítés -> short (all-in for less)
                    if delta + 1e-6 < needed:
                        short_flag[pos] = True
                else:
                    # ha a méret "to X" típus (ritkább itt), vagy nincs méret -> egész kiegészítés
                    delta = needed
            put[pos] += delta
            spent[pos] += delta
        elif move == "raises":
            if size is None: continue
            delta = max(0.0, size - put[pos])
            put[pos] += delta
            spent[pos] += delta
            max_put = max(max_put, put[pos])
        elif ('allin' in re.sub(r'[^a-z]', '', move)):
            if size is None: continue
            delta = max(0.0, size)
            put[pos] += delta
            spent[pos] += delta
            allin_flag[pos] = True
            if put[pos] > max_put:
                max_put = put[pos]
        else:
            if size is not None:
                delta = max(0.0, size)
                put[pos] += delta
                spent[pos] += delta
                if put[pos] > max_put:
                    max_put = put[pos]
    return spent, allin_flag, short_flag
