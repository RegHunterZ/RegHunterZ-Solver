from .tesseract_finder import ensure_pytesseract_cmd, debug_report
import app.safe as safe
import cv2, numpy as np, pytesseract, json, os, re
from dataclasses import dataclass
from typing import List, Dict
from .config_io import load_cfg, save_cfg
from modules.hh_ocr.hh_ocr import ocr_hh_box
from modules.hh_ocr.hh_parser import parse_hh_lines

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
os.makedirs(LOG_DIR, exist_ok=True)

DIGIT_CFG = r'--psm 7 -c tessedit_char_whitelist=0123456789.$€₿,'

def _ensure_tesseract_cmd():
    cfg = load_cfg(); cmd = safe.get(cfg, "tesseract_cmd")
    if cmd and os.path.isfile(cmd): pytesseract.pytesseract.tesseract_cmd = cmd

@dataclass
class SeatRead:
    name: str; stack: str; action: str=""

def _norm_roi(img, roi_rel):
    h,w = img.shape[:2]; x=max(int(roi_rel[0]*w),0); y=max(int(roi_rel[1]*h),0)
    rw=int(roi_rel[2]*w); rh=int(roi_rel[3]*h); x2=min(x+rw, w); y2=min(y+rh, h)
    return img[y:y2, x:x2]

def _prep(gray):
    g = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY) if len(gray.shape)==3 else gray
    _, th = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU); return th

def _clean_num(text):
    if not text: return ""; text=text.strip().replace("O","0").replace("o","0")
    return re.sub(r'[^0-9.,$€₿]+','', text)

def read_table(image_path: str, profiles_json: str, profile_name: str) -> Dict:
    _ensure_tesseract_cmd()
    with open(profiles_json,"r",encoding="utf-8") as f: profiles=json.load(f)
    prof=profiles[profile_name]
    data=np.fromfile(image_path,dtype=np.uint8); img=cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:  
    
        raise RuntimeError("Nem sikerült betölteni a képet.")
    seats_out: List[SeatRead]=[]
    for s in safe.get(prof, "seats", []):
        st_roi=_prep(_norm_roi(img, s["stack"])) if "stack" in s else None
        st=_clean_num(safe_image_to_string(st_roi, config=DIGIT_CFG)) if st_roi is not None else ""
        seats_out.append(SeatRead(safe.get(s, "name",""), st))
    pot_roi=_prep(_norm_roi(img, prof["pot"])) if safe.get(prof, "pot") else None
    pot=_clean_num(safe_image_to_string(pot_roi, config=DIGIT_CFG)) if pot_roi is not None else ""
    # HH by streets
    def _bgr(a): return cv2.cvtColor(a, cv2.COLOR_GRAY2BGR) if len(a.shape)==2 else a
    hh_data={}
    for key,label in [("hh_preflop","Preflop"),("hh_flop","Flop"),("hh_turn","Turn"),("hh_river","River")]:
        r=safe.get(prof, key)
        if isinstance(r,(list,tuple)):
            roi=_norm_roi(img, r); frame=_bgr(roi)
            lines=ocr_hh_box(frame, (0,0,frame.shape[1], frame.shape[0]))
            parsed=parse_hh_lines(lines); 
            if label in parsed: hh_data[label]=parsed[label]
    hh_by_seat={}
    for street, acts in hh_data.items():
        for a in acts:
            seat=(safe.get(a, "seat") or "").upper() or "UNK"; txt=safe.get(a, "raw") or safe.get(a, "action","")
            if txt: hh_by_seat.setdefault(seat, {}).setdefault(street, []).append(txt)
    out={"image_path":image_path,"profile":profile_name,"seats":[s.__dict__ for s in seats_out],"pot":pot,"dealer_roi":safe.get(prof, "dealer"),"hh":hh_data or None,"hh_by_seat":hh_by_seat}
    try:
        with open(os.path.join(LOG_DIR,"last_ocr.json"),"w",encoding="utf-8") as f: json.dump(out,f,indent=2,ensure_ascii=False)
    except Exception: pass
    return out


def _assert_tesseract_available():
    import logging
    cmd = ensure_pytesseract_cmd()
    if not cmd:
        logging.error('Tesseract not found. Diagnostics: %s', debug_report())
    
        raise RuntimeError(
            "Tesseract OCR nincs telepítve vagy nincs beállítva.\n"
            "Gyors telepítés Windows alatt (egyik opció):\n"
            " - winget install --id=UB-Mannheim.TesseractOCR\n"
            " - choco install tesseract --confirm\n"
            "Ha már telepítve van, állítsd be az utat: Beállítások → OCR → Tesseract elérési út,\n"
            "vagy add a PATH-hoz."
        )


def _assert_tesseract_available():
    import logging
    cmd = ensure_pytesseract_cmd()
    if not cmd:
        logging.error('Tesseract not found. Diagnostics: %s', debug_report())
    
        raise RuntimeError(
            'Tesseract OCR nincs telepítve vagy nincs beállítva. '
            'Telepítés: winget install --id=UB-Mannheim.TesseractOCR '
            'vagy choco install tesseract --confirm; '
            'vagy állítsd be az elérési utat app/config.yaml -> ocr.tesseract_path.'
        )

def safe_image_to_string(img, *args, **kwargs):
    _assert_tesseract_available()
    import pytesseract
    return safe_image_to_string(img, *args, **kwargs)
