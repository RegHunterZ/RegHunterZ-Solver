
import os, base64, json, io, time, hashlib
from dotenv import load_dotenv
from typing import List, Dict, Any, Tuple

from .hh_parser import ensure_sixmax
from .cost_saver import MAX_DIM, JPEG_QUALITY, RETRIES, BACKOFF_BASE, CACHE_FILE

# Optional local OCR
try:
    from PIL import Image
    import pytesseract
    _LOCAL_OCR_AVAILABLE = True
except Exception:
    _LOCAL_OCR_AVAILABLE = False

load_dotenv()
from openai import OpenAI, APIError, RateLimitError

_API_KEY = os.getenv("OPENAI_API_KEY")
_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")

client = None
if _API_KEY:
    client = OpenAI(api_key=_API_KEY)

def chat(messages: List[Dict[str, str]], **kwargs) -> str:
    if not client:
        raise RuntimeError("OPENAI_API_KEY missing for chat.")
    resp = client.chat.completions.create(
        model=_MODEL,
        messages=messages,
        temperature=kwargs.get("temperature", 0.2),
        max_tokens=kwargs.get("max_tokens", 800),
    )
    return resp.choices[0].message.content or ""

def _img_to_b64_downscaled(path: str) -> Tuple[str, str]:
    """Downscale and compress image for cheaper API calls. Returns (mime, b64)."""
    with Image.open(path) as im:
        im = im.convert("RGB")
        w, h = im.size
        scale = 1.0
        if max(w, h) > MAX_DIM:
            scale = MAX_DIM / float(max(w, h))
            im = im.resize((int(w*scale), int(h*scale)))
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        data = buf.getvalue()
    b64 = base64.b64encode(data).decode("utf-8")
    return "image/jpeg", b64

def _cache_path(base_dir: str) -> str:
    return os.path.join(base_dir, CACHE_FILE)

def _hash_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def _read_cache(base_dir: str) -> Dict[str, Any]:
    p = _cache_path(base_dir)
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _write_cache(base_dir: str, cache: Dict[str, Any]) -> None:
    try:
        with open(_cache_path(base_dir), "w", encoding="utf-8") as f:
            json.dump(cache, f)
    except Exception:
        pass

def _cloud_vision(image_path: str) -> Dict[str, Any]:
    if not client:
        raise RuntimeError("OPENAI_API_KEY missing for vision.")
    mime, b64 = _img_to_b64_downscaled(image_path)
    SYSTEM = (
        "You convert poker screenshots into (1) clean hand history text and (2) a strict JSON object. "
        "Use 6-max positions (UTG, HJ, CO, BTN, SB, BB). Sizes are in big blinds."
    )
    USER_TEXT = (
        "1) Provide plain HH text (players/stacks and Preflop/Flop/Turn/River actions). "
        "2) ALSO provide a STRICT JSON with this schema:\n"
        "{\n"
        '  "players": {"BTN":{"pos":"BTN","stack":100.0}, ...},\n'
        '  "actions": [{"street":"Preflop","pos":"BTN","move":"opens","size":2.5}, ...]\n'
        "}\n"
        "IMPORTANT: First output the HH text between <HH>...</HH>, then output the JSON between <JSON>...</JSON>."
    )
    messages = [
        {"role":"system","content":SYSTEM},
        {"role":"user","content":[
            {"type":"text","text":USER_TEXT},
            {"type":"image_url","image_url":{"url":f"data:{mime};base64,{b64}"}}
        ]}
    ]

    last_err = None
    for i in range(max(1, RETRIES)):
        try:
            resp = client.chat.completions.create(
                model=_MODEL,
                messages=messages,
                temperature=0,
                max_tokens=1600,
            )
            content = resp.choices[0].message.content or ""
            def _ext(tag):
                s = content.find(f"<{tag}>"); e = content.find(f"</{tag}>")
                return content[s+len(tag)+2:e].strip() if (s!=-1 and e!=-1 and e>s) else ""
            hh_text = _ext("HH")
            js = _ext("JSON")
            parsed = {"players":{}, "actions":[]}
            if js:
                try:
                    obj = json.loads(js)
                    if isinstance(obj, dict): parsed = obj
                except Exception: pass
            return {"hh_text": hh_text, "parsed": parsed}
        except RateLimitError as e:
            last_err = e; time.sleep((BACKOFF_BASE ** i))
        except APIError as e:
            last_err = e
            if getattr(e, "status_code", None) == 429:
                time.sleep((BACKOFF_BASE ** i))
            else:
                break
        except Exception as e:
            last_err = e; break
    raise last_err if last_err else RuntimeError("Vision failed")

def _local_ocr(image_path: str) -> str:
    if not _LOCAL_OCR_AVAILABLE:
        raise RuntimeError("Local OCR not available (Pillow/pytesseract missing).")
    try:
        # Requires Tesseract installed on the system PATH
        txt = pytesseract.image_to_string(Image.open(image_path))
        return txt
    except Exception as e:
        raise RuntimeError(f"Local OCR error: {e}")

def analyze_image(image_path: str, mode: str = "cloud_first", base_dir: str = None) -> Dict[str, Any]:
    """mode in {'cloud_first','local_first','local_only'}. Caching by image hash."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(image_path)
    if base_dir is None:
        base_dir = os.path.dirname(os.path.dirname(__file__))

    cache = _read_cache(base_dir)
    key = _hash_file(image_path) + f"::{mode}::{_MODEL}"
    if key in cache:
        return cache[key]

    def _post(hh_text: str, parsed: Dict[str, Any]) -> Dict[str, Any]:
        out = {"hh_text": hh_text or "", "parsed": ensure_sixmax(hh_text or "", parsed or {"players":{}, "actions":[]})}
        cache[key] = out; _write_cache(base_dir, cache); return out

    if mode == "local_only":
        hh = _local_ocr(image_path); return _post(hh, {"players":{}, "actions":[]})

    if mode == "local_first":
        try:
            hh = _local_ocr(image_path); return _post(hh, {"players":{}, "actions":[]})
        except Exception:
            res = _cloud_vision(image_path); return _post(res.get("hh_text",""), res.get("parsed", {}))

    # cloud_first
    try:
        res = _cloud_vision(image_path); return _post(res.get("hh_text",""), res.get("parsed", {}))
    except Exception:
        hh = _local_ocr(image_path); return _post(hh, {"players":{}, "actions":[]})
