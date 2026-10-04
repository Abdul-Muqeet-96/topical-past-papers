"""Check 6 (automated part 1): enumerate every placed crop band (Form XObject wrapping a source
page, BBox = clip) on every book page; map each band to its source page by text overlap; flag
(a) text clipped at band edges (source words partly inside the clip), (b) band text not from the
item's own paper, (c) footer/header text inside a band."""
import pymupdf as f, json, re, sys, glob
from collections import defaultdict, Counter
B='Δ-chemistry/p2-topical-workbook/Chemistry-9701-P2-Topical-Workbook.pdf'
d=f.open(B)
bi=json.load(open('audit/out/book_items.json'))
SER={'M/J':'s','O/N':'w','MAR':'m'}
def pk(ref): m=re.match(r'(M/J|O/N|MAR) (\d\d)/P(\d\d)',ref); return f"{SER[m.group(1)]}{m.group(2)}",m.group(3)
heads=defaultdict(list)
for it in bi: heads[it['page']].append(it)
# item owning a y position on a page: last heading above it (or last item of previous page)
seq=sorted(bi,key=lambda i:(i['page'],i['y']))
def owner(pg,y):
    best=None
    for it in seq:
        if (it['page'],it['y'])<=(pg,y): best=it
        else: break
    return best
srccache={}
def src(fn):
    if fn not in srccache:
        D=f.open(fn); srccache[fn]=(D,[ [ (w[0],w[1],w[2],w[3],w[4]) for w in p.get_text('words')] for p in D])
    return srccache[fn]
def toks(s): return [t for t in re.findall(r'[A-Za-z]{3,}|\d+',s)]
bands=[]; xmap={}
import bisect
idx_keys=[(i['page'],i['y']) for i in seq]
for pno in range(len(d)):
    p=d[pno]
    for xref,name,inv,bbox in p.get_xobjects():
        if inv: continue   # nested form (fix branch: a re-scaled source page wrapped in an A4 page)
        obj=d.xref_object(xref)
        if '/fullpage' not in obj: continue
        m=re.search(r'/BBox \[ ([\d.\-]+) ([\d.\-]+) ([\d.\-]+) ([\d.\-]+) \]',obj)
        clip=[float(x) for x in m.groups()]
        fp=int(re.search(r'/fullpage (\d+) 0 R',obj).group(1))
        H=p.rect.height; tr=f.Rect(bbox[0],H-bbox[3],bbox[2],H-bbox[1])
        k=bisect.bisect_right(idx_keys,(pno+1,(tr.y0+tr.y1)/2))-1
        it=seq[k] if k>=0 else None
        txt=p.get_text(clip=tr+(1,1,-1,-1))
        bands.append({'page':pno+1,'target':list(tr),'clip':clip,'fp':fp,'ref':it['ref'] if it else None,'side':it['side'] if it else None,'text':txt})
print('bands',len(bands))
# map fullpage xref -> (file,page) using text overlap within the item's paper (qp for Q side, ms for A side, try both)
def candidates(ref):
    s,v=pk(ref); return [f'data/9701_{s}_qp_{v}.pdf',f'data/9701_{s}_ms_{v}.pdf']
fptext=defaultdict(str); fpref={}
for b in bands: fptext[b['fp']]+=' '+b['text']; fpref.setdefault(b['fp'],b['ref'])
fpsrc={}
for fp,t in fptext.items():
    T=set(toks(t)); best=(0,None)
    if not T: fpsrc[fp]=None; continue
    for fn in candidates(fpref[fp]):
        D,W=src(fn)
        for i,ws in enumerate(W):
            S=set(toks(' '.join(w[4] for w in ws)))
            ov=len(T&S)/max(1,len(T))
            if ov>best[0]: best=(ov,(fn,i))
    fpsrc[fp]={'match':best[1],'overlap':round(best[0],3)}
# fix branch: the build normalises re-scaled question papers to A4 before cropping, so band clips
# are in A4 coordinates. Map them back to the raw source page. Scale is measured here independently
# from the top page-number position (centred at x = width/2 on a standard page).
def raw_scale(fn):
    D,_=src(fn); ks=[]
    for p in D:
        for w in p.get_text('words'):
            if w[1]<0.08*p.rect.height and re.fullmatch(r'\d{1,2}',w[4]):
                ks.append(((w[0]+w[2])/2)/297.64)
    ks.sort(); k=ks[len(ks)//2] if ks else 1.0
    return k if abs(k-1)>0.03 else 1.0
kcache={}
for b in bands:
    m=fpsrc.get(b['fp'])
    if not m or not m['match'] or '_qp_' not in m['match'][0]: continue
    fn,pi=m['match']
    if fn not in kcache: kcache[fn]=raw_scale(fn)
    k=kcache[fn]
    if k==1.0: continue
    Hr=src(fn)[0][pi].rect.height; c=b['clip']
    t=[c[0]*k,(841.89-c[3])*k,c[2]*k,(841.89-c[1])*k]
    b['clip']=[t[0],Hr-t[3],t[2],Hr-t[1]]; b['scaled']=k
print('re-scaled papers',{k:round(v,3) for k,v in kcache.items() if v!=1.0})
json.dump({'bands':bands,'fpsrc':{str(k):v for k,v in fpsrc.items()}},open('audit/out/bands.json','w'))
lo=[(fp,v) for fp,v in fpsrc.items() if v and v['overlap']<0.8]
print('source pages placed',len(fpsrc),'; low-overlap mappings',len(lo), lo[:5])
