import json, os
CFG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
def load_cfg():
    if os.path.exists(CFG_FILE):
        try:
            with open(CFG_FILE,"r",encoding="utf-8") as f: return json.load(f)
        except Exception: return {}
    return {}
def save_cfg(cfg: dict):
    try:
        with open(CFG_FILE,"w",encoding="utf-8") as f: json.dump(cfg,f,indent=2,ensure_ascii=False)
    except Exception: pass
