
import os, sys, shutil
from pathlib import Path
import platform

def candidates():
    env = os.environ
    paths = []

    # From env var
    if "TESSERACT_CMD" in env:
        paths.append(env["TESSERACT_CMD"])

    # Common Windows install locations
    program_files = env.get("ProgramFiles", r"C:\Program Files")
    program_files_x86 = env.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    local_appdata = env.get("LOCALAPPDATA", r"C:\Users\%USERNAME%\AppData\Local")
    chocolatey = r"C:\ProgramData\chocolatey\bin\tesseract.exe"

    defaults = [
        Path(program_files) / "Tesseract-OCR" / "tesseract.exe",
        Path(program_files_x86) / "Tesseract-OCR" / "tesseract.exe",
        Path(local_appdata) / "Programs" / "Tesseract-OCR" / "tesseract.exe",
        Path(chocolatey),
    ]

    paths += [str(p) for p in defaults]

    # If PATH contains tesseract
    on_path = shutil.which("tesseract.exe") or shutil.which("tesseract")
    if on_path:
        paths.insert(0, on_path)

    # Look in current bundle (portable)
    here = Path(__file__).resolve().parent.parent
    portable = here / "bin" / "tesseract" / "tesseract.exe"
    paths.insert(0, str(portable))

    # Any extra hints from config.yaml
    try:
        import yaml
        cfg_file = here / "config.yaml"
        if cfg_file.exists():
            cfg = yaml.safe_load(cfg_file.read_text(encoding="utf-8")) or {}
            hint = (cfg.get("ocr") or {}).get("tesseract_path")
            if hint:
                paths.insert(0, hint)
    except Exception:
        pass

    # Remove duplicates while preserving order
    seen = set()
    uniq = []
    for p in paths:
        if p and p not in seen:
            uniq.append(p)
            seen.add(p)
    return uniq

def find_tesseract():
    if platform.system().lower() != "windows":
        # rely on PATH
        from shutil import which
        cmd = which("tesseract")
        return cmd

    for p in candidates():
        try:
            if p and Path(p).exists():
                return str(Path(p))
        except Exception:
            continue
    return None

def ensure_pytesseract_cmd():
    try:
        import pytesseract
        cmd = find_tesseract()
        if cmd:
            pytesseract.pytesseract.tesseract_cmd = cmd
            return cmd
    except Exception:
        pass
    return None


def debug_report():
    import os
    cand = candidates()
    path_env = os.environ.get('PATH','')
    return {'found': find_tesseract(), 'candidates': cand, 'PATH': path_env}
