
from typing import Dict, List, Tuple, Iterable

RANKS = ["A","K","Q","J","T","9","8","7","6","5","4","3","2"]

def hand_name(r: int, c: int) -> str:
    # 13x13 matrix, excluding labels row/col; r,c in [0..12] where 0 -> A, 12 -> 2
    # pairs on diagonal, suited below, offsuit above (AKs is row K col A in standard top-left AA layout),
    # but our input is always the conventional 13x13 with AA at (0,0)
    ra = RANKS[r]
    rb = RANKS[c]
    if r == c:
        return f"{ra}{rb}"
    elif r < c:
        # top-right triangle = offsuit (e.g., AKo at row A col K)
        return f"{ra}{rb}o"
    else:
        # bottom-left triangle = suited (e.g., AKs at row K col A)
        return f"{ra}{rb}s"

def flatten_selected_cells(selected: Iterable[Tuple[int,int]]) -> List[str]:
    # selected -> list of (row, col) 0-based in the 13x13 actual grid (AA..22)
    hands = [hand_name(r, c) for (r, c) in selected]
    # keep a stable order that's readable: Pairs top-down, suited/offsuit by top-left to bottom-right scan
    # Sort key: pairs first by rank index, then suited, then offsuit
    rank_index = {r:i for i,r in enumerate(RANKS)}
    def sort_key(h: str):
        if len(h) == 2: # pair
            return (0, rank_index[h[0]])
        # len=3 with s/o
        a, b, t = h[0], h[1], h[2]
        if t == "s":
            return (1, rank_index[a], rank_index[b])
        return (2, rank_index[a], rank_index[b])
    hands.sort(key=sort_key)
    return hands

def compact_list(hands: List[str]) -> str:
    # Keep simple comma-separated list; avoid complex range-merging that could hide edge cases
    return ", ".join(hands)
