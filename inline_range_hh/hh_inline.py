
from typing import Dict, List, Tuple
import re
from .range_util import compact_list

ACTION_KEYS = [
    # order matters to avoid "bets" capturing "bet" etc.
    "opens", "raises", "bets", "calls", "checks", "folds", "3bets", "4bets", "5bets"
]

def inject_ranges_into_hh(hh_text: str, assigned_ranges: Dict[str, List[str]]) -> str:
    """
    Append selected range (hands list) next to each manual action line in the HH text.

    Params
    ------
    hh_text: str
        The full HH text (multi-line), e.g. "UTG bets 3", "BB raises 2", etc.
    assigned_ranges: Dict[str, List[str]]
        Key by the exact action identifier you use in the UI, e.g.:
            "UTG bets": ["AKs", "AQs", "TT", "AKo"]
            "BB raises": ["A5s", "KQo"]
        Values must be a list of hand codes (AA, AKs, AKo, etc.).

    Returns
    -------
    str: updated HH where each matching action line gets " [range: ...]" appended once.
    """
    lines = hh_text.splitlines()
    out = []
    for ln in lines:
        stripped = ln.strip()
        appended = False
        for key, hands in assigned_ranges.items():
            # match if the line starts with the key (e.g., "UTG bets") possibly followed by numbers/words
            if stripped.startswith(key):
                if hands:
                    rng = compact_list(hands)
                    ln = f"{ln} [range: {rng}]"
                appended = True
                break
        out.append(ln)
    return "\n".join(out)

def normalize_ui_ranges(raw_ranges: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Passthrough today; reserved for future normalization/validation if needed.
    """
    return raw_ranges
