
from ai_coach.inline_range_hh import inject_ranges_into_hh

sample_hh = """**Players and Stacks:**
- UTG: Stack 100 BB
- HJ: Stack 100 BB
- CO: Stack 100 BB
- BTN: Stack 100 BB
- SB: Stack 100 BB
- BB: Stack 100 BB

**Preflop Actions:**
- UTG bets 3
- BB raises 2
- UTG calls 8
"""

# Suppose these are the ranges the user selected in the range-table UI for each action:
assigned = {
    "UTG bets": ["AKs", "AQs", "JJ", "TT", "AKo", "AQo"],
    "BB raises": ["A5s", "KQo", "99", "AJo"],
    "UTG calls": ["KQs", "QJs", "88", "ATs"]
}

print(inject_ranges_into_hh(sample_hh, assigned))
