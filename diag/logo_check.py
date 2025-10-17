
from __future__ import annotations
import os, sys, platform, json
from typing import Dict, List
from PyQt6.QtGui import QPixmap, QImageReader

CANDIDATE_FILENAMES = [
    'logo.png',
    'reghuterz-hatternelkul_1.png',
    'reghuterz-hatternelkul (1).png',
]

def _candidate_paths() -> List[str]:
    paths = []
    env = os.environ.get('RHZ_LOGO')
    if env: paths.append(env)
    here = os.path.dirname(__file__)
    assets = os.path.abspath(os.path.join(here, '..','assets'))
    for name in CANDIDATE_FILENAMES:
        paths.append(os.path.join(assets, name))
    return paths

def run_logo_diagnostics() -> Dict:
    report = {
        "python": sys.version,
        "platform": platform.platform(),
        "cwd": os.getcwd(),
        "env_RHZ_LOGO": os.environ.get("RHZ_LOGO", ""),
        "qt_image_formats": sorted(set([bytes(fmt).decode('ascii','ignore') for fmt in QImageReader.supportedImageFormats()])),
        "candidates": [],
        "loaded_ok": False,
        "loaded_path": "",
        "pixmap_is_null": True,
        "pixmap_size": (0,0),
    }
    for p in _candidate_paths():
        exists = os.path.exists(p)
        readable = False
        size = (0,0)
        ok = False
        if exists:
            pm = QPixmap(p)
            readable = True
            ok = not pm.isNull()
            if ok:
                size = (pm.width(), pm.height())
                if not report["loaded_ok"]:
                    report["loaded_ok"] = True
                    report["loaded_path"] = p
                    report["pixmap_is_null"] = False
                    report["pixmap_size"] = size
        report["candidates"].append({"path": p, "exists": exists, "readable": readable, "load_ok": ok, "size": size})
    return report

def report_text() -> str:
    r = run_logo_diagnostics()
    lines = []
    lines.append(f"Python: {r['python']}")
    lines.append(f"Platform: {r['platform']}")
    lines.append(f"Working dir: {r['cwd']}")
    lines.append(f"RHZ_LOGO: {r['env_RHZ_LOGO']}")
    lines.append(f"Qt image formats: {', '.join(r['qt_image_formats'])}")
    lines.append("Candidates:")
    for c in r["candidates"]:
        lines.append(f"  - {c['path']} | exists={c['exists']} load_ok={c['load_ok']} size={c['size']}")
    if r["loaded_ok"]:
        lines.append(f"Loaded: {r['loaded_path']} size={r['pixmap_size']}")
    else:
        lines.append("Loaded: <NONE>")
    return "\n".join(lines)
