
from typing import Dict, Any
from .api import chat

SYSTEM = (
    "You are a poker coach focused on KKPoker 6-max cash games. "
    "Be concise, give actionable tips tied to positions, stacks, and sizes."
)

def coach_reply(parsed: Dict[str, Any], user_msg: str) -> str:
    players_txt = ", ".join(f"{p.get('pos')}: {p.get('name', '')} {p.get('stack')}bb".strip() for p in parsed.get('players', {}).values())
    actions_txt = "; ".join(
        f"{a['street']} {a['pos']} {a['move']}" + (f" {a['size']}bb" if a.get('size') else "")
        for a in parsed.get('actions', [])
    )
    context = f"Players: {players_txt}\nActions: {actions_txt}"
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"Hand context (parsed):\n{context}\n\nUser: {user_msg}"},
    ]
    return chat(messages)
