import app.safe as safe
import os, cv2, numpy as np
try:
    import pytesseract
except ImportError:
    pytesseract=None
def _ensure_tesseract():
    if pytesseract is None: raise RuntimeError("pytesseract nincs telepitve. pip install pytesseract")
    p=safe.get(os.environ, "TESS_PATH"); 
    if p and os.path.exists(p): pytesseract.pytesseract.tesseract_cmd=p
def preprocess_hh_roi(img_roi: np.ndarray)->np.ndarray:
    gray=cv2.cvtColor(img_roi, cv2.COLOR_BGR2GRAY); gray=cv2.bilateralFilter(gray,5,50,50)
    th=cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,31,6)
    if (th>0).mean()>0.5: th=cv2.bitwise_not(th)
    return th
def ocr_hh_box(full_frame_bgr: np.ndarray, roi: tuple[int,int,int,int]):
    _ensure_tesseract(); x,y,w,h=roi; crop=full_frame_bgr[y:y+h, x:x+w].copy()
    proc=preprocess_hh_roi(crop); cfg=r'--oem 3 --psm 6 -l eng'; cfg+=' -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.+-/:,()$% '
    import pytesseract as pt
    data=pt.image_to_data(proc, config=cfg, output_type=pt.Output.DICT)
    lines=[]; cur=[]; last=None
    for i in range(len(data["text"])):
        txt=data["text"][i].strip(); conf=float(data["conf"][i]) if data["conf"][i]!="-1" else -1.0
        if not txt and conf<0: continue
        ln=data["line_num"][i]; bbox=(int(data["left"][i]),int(data["top"][i]),int(data["width"][i]),int(data["height"][i]))
        if last is None or ln==last: cur.append((txt,conf,bbox))
        else: lines.append(_merge(cur)); cur=[(txt,conf,bbox)]
        last=ln
    if cur: lines.append(_merge(cur)); return lines
def _merge(parts):
    texts=[t for (t,_,__) in parts if t]; confs=[c for (_,c,__) in parts if c>=0]
    avg=sum(confs)/len(confs) if confs else 0.0; full=" ".join(texts)
    xs=[bx for (_,_,(bx,by,bw,bh)) in parts]; ys=[by for (_,_,(bx,by,bw,bh)) in parts]; ws=[bw for (_,_,(bx,by,bw,bh)) in parts]; hs=[bh for (_,_,(bx,by,bw,bh)) in parts]
    if xs: x=min(xs); y=min(ys); w=max([xs[i]+ws[i] for i in range(len(xs))])-x; h=max([ys[i]+hs[i] for i in range(len(ys))])-y
    else: x=y=w=h=0
    return {"text":full,"conf":round(avg,2),"bbox":(x,y,w,h)}
