import cv2, json, sys
from modules.hh_ocr.hh_ocr import ocr_hh_box
from modules.hh_ocr.hh_parser import parse_hh_lines
def main(img_path, x, y, w, h, out="hh_demo.json"):
    frame = cv2.imread(img_path)
    lines = ocr_hh_box(frame, (int(x), int(y), int(w), int(h)))
    hh = parse_hh_lines(lines)
    with open(out,"w",encoding="utf-8") as f: json.dump(hh, f, ensure_ascii=False, indent=2)
    print("Wrote", out)
if __name__=="__main__":
    if len(sys.argv)<6:
        print("Usage: python run_hh_ocr_demo.py <image> <x> <y> <w> <h> [out.json]"); sys.exit(1)
    main(*sys.argv[1:6], *(sys.argv[6:] or []))
