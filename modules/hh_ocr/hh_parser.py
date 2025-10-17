import app.safe as safe
import re
REPLACEMENTS=[(r'\b8B\b','BB'),(r'All[\-\u2013\u2014 ]?in','All-in'),(r'\s+',' ')]
STREET_HEADERS=['Preflop','Flop','Turn','River']
ACTION_PATTERNS=[
    (re.compile(r'\b(Check|Fold)\b', re.I), lambda m: {'action':m.group(1).capitalize()}),
    (re.compile(r'\b(Bet)\s*([0-9]+(?:\.[0-9]+)?)\s*BB\b', re.I), lambda m:{'action':'Bet','size_bb':float(m.group(2))}),
    (re.compile(r'\b(Raise)\s*([0-9]+(?:\.[0-9]+)?)\s*BB\b', re.I), lambda m:{'action':'Raise','size_bb':float(m.group(2))}),
    (re.compile(r'\b(Call)\s*([0-9]+(?:\.[0-9]+)?)\s*BB\b', re.I), lambda m:{'action':'Call','size_bb':float(m.group(2))}),
    (re.compile(r'\b(All\-?in)\s*([0-9]+(?:\.[0-9]+)?)\s*BB\b', re.I), lambda m:{'action':'All-in','size_bb':float(m.group(2))}),
    (re.compile(r'\b(Wins?)\s*([0-9]+(?:\.[0-9]+)?)\s*BB\b', re.I), lambda m:{'action':'Win','size_bb':float(m.group(2))}),
]
def _clean_text(s:str)->str:
    out=s
    for pat,repl in REPLACEMENTS: out=re.sub(pat,repl,out)
    return out.strip()
def parse_hh_lines(ocr_lines):
    texts=[]
    for ln in ocr_lines:
        t=_clean_text(safe.get(ln, 'text',''))
        if not t: continue
        texts.append({'text':t,'conf':safe.get(ln, 'conf',0)})
    street='Preflop'; out={s:[] for s in STREET_HEADERS}
    for item in texts:
        t=item['text']
        for header in STREET_HEADERS:
            if re.search(rf'\b{header}\b',t,re.I):
                street=header; t=re.sub(rf'\b{header}\b','',t,flags=re.I).strip(' :'); 
                if not t: break
        if not t: continue
        m=re.match(r'(?:(?P<seat>SB|BB|UTG|HJ|CO|BTN|MP|EP)\b)\s*(?P<rest>.*)',t,re.I)
        seat=None; rest=t
        if m: seat=m.group('seat').upper(); rest=m.group('rest').strip()
        act={'seat':seat,'raw':t,'conf':item['conf']}; matched=False
        for rx,b in ACTION_PATTERNS:
            mm=rx.search(rest)
            if mm: act.update(b(mm)); matched=True; break
        out[street].append(act)
    return {k:v for k,v in out.items() if v}
