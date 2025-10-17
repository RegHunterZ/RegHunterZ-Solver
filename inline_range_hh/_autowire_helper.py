
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
