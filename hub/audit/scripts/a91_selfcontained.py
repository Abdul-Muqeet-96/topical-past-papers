"""Check 7 SELF-CONTAINMENT on the question side of every item (visible text from a90).
(1) stem: the source question stem (text between the question number and its first lettered part,
    from my own QP reading) must appear in the item; (2) every 'Table n.n'/'Fig. n.n'/'Figure n.n'
    mentioned must have its caption in the item; (3) part references '(x)', '(x)(y)', 'part (x)',
    'your answer to (x)' must point to a part shown in the item; (4) single-letter labels used
    as 'compound X'/'element X'/... must also occur elsewhere in the item (defined); (5) reliance on
    the Data Booklet / Periodic Table."""
import json, re, sys, pymupdf as f
sys.path.insert(0,'audit/scripts'); from a03_lines import lines
from a31_coverage import pkey
qp=json.load(open('audit/out/qp_parse.json')); IT=json.load(open('audit/out/item_text.json'))
SER={'s':'s','w':'w','m':'m'}
stems={}
def stem(k,q):
    if (k,q) in stems: return stems[(k,q)]
    s,v=k.split('_'); d=f.open(f'data/9701_{s}_qp_{v}.pdf')
    pg,y=[(p,yy) for (qq,p,yy) in qp[k]['qpos'] if qq==q][0]
    txt=[]; started=False
    for pno in range(pg-1,min(pg+1,len(d))):
        p=d[pno]; sc=p.rect.width/595.28
        for l in lines(p):
            if pno==pg-1 and l['c']/sc<y-3: continue
            W=[w for w in l['w'] if 30<=w[0]/sc<=570]
            if not W: continue
            t=' '.join(w[4] for w in W)
            if re.match(r'(\d+\s+)?\([a-z]\)',t) : stems[(k,q)]=' '.join(txt); return stems[(k,q)]
            if l['c']/sc>785 or 'UCLES' in t: continue
            txt.append(re.sub(r'^\d+\s+','',t) if not txt else t)
    stems[(k,q)]=' '.join(txt); return stems[(k,q)]
def norm(s): return re.sub(r'[^a-z0-9]','',s.lower())
res=[]
for key,v in IT.items():
    if v['side']!='Q': continue
    ref=v['ref']; k,q,suf=pkey(ref); t=v['text']; issues=[]
    st=stem(k,q); stw=[w for w in re.findall(r'[A-Za-z]{4,}',st) if not re.fullmatch(r'[.…]+',w)]
    if len(stw)>=3:
        nt=norm(t); hit=sum(1 for w in stw if norm(w) in nt)/len(stw)
        if hit<0.6: issues.append(('stem missing',st[:80]))
    for m in set(re.findall(r'\b(Table|Fig\.|Figure)\s+(\d+\.\d+)',t)):
        cap=rf'(?m)^\s*{re.escape(m[0])}\s+{re.escape(m[1])}\s*(\(not to scale\))?\s*$'
        if not re.search(cap,t): issues.append(('dangling '+m[0],m[1]))
    own=set(re.findall(r'\(([a-z])\)',suf))
    shown=set(re.findall(r'(?:^|\s)\(([a-h])\)\s',t))
    for m in re.finditer(r'(?:in|to|from|of|part|answer to|answers to|calculated in|identified in|shown in|given in|described in)\s+\(([a-h])\)(\([ivx]+\))?',t):
        if m.group(1) not in shown and m.group(1) not in own: issues.append(('dangling part ref',m.group(0)))
    for m in set(re.findall(r'\b(?:compound|element|ion|isomer|molecule|substance|salt|gas|product|solution|reagent|reaction|metal|acid|alcohol|ester|polymer|oxide)\s+([A-Z])\b(?!\w)',t)):
        if len(re.findall(rf'(?<![\w/(]){m}(?![\w+–−])',t))<2: issues.append(('label used once',m))
    if re.search(r'Data Booklet',t): issues.append(('needs Data Booklet',''))
    if re.search(r'Periodic Table',t) and not re.search(r'Periodic Table of',t): issues.append(('mentions Periodic Table',''))
    res.append({'ref':ref,'page':v['page'],'unit':v['unit'],'issues':issues})
json.dump(res,open('audit/out/selfcontained.json','w'),indent=0)
from collections import Counter
c=Counter(i[0] for r in res for i in r['issues']); print('items',len(res),'with issues',sum(1 for r in res if r['issues']),dict(c))
for r in res:
    for i in r['issues']:
        if i[0]!='stem missing': print(r['ref'],r['page'],i)
