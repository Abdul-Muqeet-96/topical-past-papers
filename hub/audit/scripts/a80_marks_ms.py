"""Check 5 MARKS + MS crops. (a) index.csv marks vs MY QP marks vs MY MS marks for the item's leaves.
(b) every MS line belonging to the item's leaves (my MS parse, incl. Guidance column and rows
continuing on the next page) must be inside the item's answer-side crops -> else TRUNCATED.
(c) MS lines shown in the answer crops that belong to other questions/parts (not the item's own
parts and not its listed context parts) -> WRONG/EXTRA ROWS."""
import json, csv, re, sys, pymupdf as f
sys.path.insert(0,'hub/audit/scripts')
from a31_coverage import pkey, expand
from a21_ms_parse import parse_ms
from collections import defaultdict
qp=json.load(open('hub/audit/out/qp_parse.json')); ms=json.load(open('hub/audit/out/ms_parse.json'))
idx={r['reference']:r for r in csv.DictReader(open('Δ-chemistry/booklets/p2-topical-workbook/index.csv'))}
B=json.load(open('hub/audit/out/bands.json')); fps=B['fpsrc']
bands=defaultdict(list)
for b in B['bands']:
    m=fps.get(str(b['fp']))
    if m and m['match'] and b['side']=='A': bands[b['ref']].append((m['match'][0],m['match'][1],b['clip'],b['page']))
mscache={}
def msl(k):
    if k not in mscache:
        s,v=k.split('_'); mscache[k]=parse_ms(f'hub/data/9701_{s}_ms_{v}.pdf')
    return mscache[k]
doc={}
def H(fn,pi):
    if fn not in doc: doc[fn]=f.open(fn)
    p=doc[fn][pi]; return p.rect.height
def lab(q,L,R): return f"{q}"+(f"({L})" if L else '')+(f"({R})" if R else '')
marks_bad=[]; trunc=[]; extra=[]; checked=0
for ref,row in idx.items():
    k,q,suf=pkey(ref); P=qp[k]['parts'][str(q)]; leaves=expand(q,suf,list(P))
    qm=sum(P[x] for x in leaves); M=ms.get(k,{}).get('parts',{}).get(str(q),{})
    # MS marks: leaf-level where labelled, else letter-level if the item covers the whole letter
    mm=0; ok=True
    for x in leaves:
        if x in M: mm+=M[x]
        else:
            Lr=re.match(r'\d+\([a-z]\)',x); Lr=Lr.group(0) if Lr else None
            if Lr in M and all(y in leaves for y in P if y.startswith(Lr)): pass
            else: ok=False
    for Lr in set(re.match(r'\d+\([a-z]\)',x).group(0) for x in leaves if re.match(r'\d+\([a-z]\)',x)):
        if Lr in M and Lr not in leaves and all(y in leaves for y in P if y.startswith(Lr)): mm+=M[Lr]
    im=int(row['marks'])
    if im!=qm or (ok and mm!=qm): marks_bad.append({'ref':ref,'index_marks':im,'my_qp':qm,'my_ms':mm if ok else None,'page':row['page']})
    # MS crop completeness
    ctx=[c.strip() for c in row['context_parts'].split(';') if c.strip()] if row['context_parts'] else []
    res=msl(k); bs=bands.get(ref,[])
    if not bs: trunc.append({'ref':ref,'issue':'no answer crop found'}); continue
    checked+=1
    want=set(leaves)
    ctxleaves=set()
    for c in ctx:
        e=expand(q,c if c.startswith('(') else c[c.index('('):] if '(' in c else '',list(P)) or []
        ctxleaves|=set(e)
    miss=0; missw=[]; ext=defaultdict(int)
    for (qq,L,R,pno,ws) in res['lines']:
        if qq is None: continue
        lt=' '.join(w[4] for w in ws)
        if re.search(r'Trace ID|Re-uploading|apaCambridge|apacambridge|©|Page \d+ of|PUBLISHED|Mark Scheme|^Question Answer|9701/\d\d|UCLES|Total:',lt): continue
        l=lab(qq,L,R)
        if L is None: continue   # label not resolved to a part (e.g. MS typo '2c(i)'): skip, ambiguous
        mine = (qq==q) and (l in want or any(x.startswith(l+'(') or l.startswith(x+'(') for x in want) or l==f'{q}' and False)
        cl=[c for (fn,pi,c,_) in bs if pi==pno and fn.endswith(f'_ms_{k.split("_")[1]}.pdf') and f'_{k.split("_")[0]}_' in fn]
        Hh=H(f'hub/data/9701_{k.split("_")[0]}_ms_{k.split("_")[1]}.pdf',pno) if cl else None
        def inside(w):
            cx,cy=(w[0]+w[2])/2,(w[1]+w[3])/2
            return any(c[0]<=cx<=c[2] and Hh-c[3]<=cy<=Hh-c[1] for c in cl)
        if mine:
            for w in ws:
                if not inside(w): miss+=1; missw.append(w[4])
        else:
            if cl and any(inside(w) for w in ws):
                isctx = (qq==q) and (l in ctxleaves or any(x.startswith(l+'(') or l.startswith(x+'(') for x in ctxleaves))
                if not isctx: ext[l]+=1
    if miss: trunc.append({'ref':ref,'page_q':row['page'],'missing_words':miss,'sample':missw[:8]})
    if ext: extra.append({'ref':ref,'page_q':row['page'],'other_rows_shown':dict(ext)})
json.dump({'marks_bad':marks_bad,'trunc':trunc,'extra':extra},open('hub/audit/out/marks_ms.json','w'),indent=0)
print('items',len(idx),'answer crops checked',checked)
print('marks mismatches',len(marks_bad)); [print(' ',x) for x in marks_bad[:15]]
print('truncated MS rows',len(trunc)); [print(' ',x) for x in trunc[:15]]
print('extra/wrong MS rows',len(extra)); [print(' ',x) for x in extra[:15]]
