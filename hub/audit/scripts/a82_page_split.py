"""Check 6 (automated part 13): figures/tables split across book pages. Consecutive bands of one item
that come from the same source page and are contiguous (or nearly, <=40 pt apart) in the source, but are
placed on different book pages, where ink crosses the cut (dark source pixels within 1.5 pt on both
sides of the cut, in the same columns) -> a figure/table is broken over a page break."""
import pymupdf as f, json
from collections import defaultdict
o=json.load(open('hub/audit/out/bands.json')); fps=o['fpsrc']; cache={}; rend={}
def page(fn,i):
    if fn not in cache: cache[fn]=f.open(fn)
    return cache[fn][i]
grp=defaultdict(list)
for b in o['bands']:
    m=fps.get(str(b['fp']))
    if m and m['match'] and b['page']!=1273: grp[(b['ref'],b['side'],m['match'][0],m['match'][1])].append(b)
Z=150/72; out=[]
for (ref,side,fn,pi),bs in grp.items():
    p=page(fn,pi); H=p.rect.height
    bs=sorted(bs,key=lambda b:H-b['clip'][3])
    for a,b in zip(bs,bs[1:]):
        if a['page']==b['page']: continue
        ya=H-a['clip'][1]; yb=H-b['clip'][3]
        if not (-1<yb-ya<=40): continue
        if (fn,pi) not in rend: rend[(fn,pi)]=p.get_pixmap(dpi=150,colorspace=f.csGRAY)
        pm=rend[(fn,pi)]; W=pm.width; s=pm.samples; x0,x1=int(42*Z),int(553*Z)
        def dk(y):
            yy=int(y*Z); return set(x for x in range(x0,min(x1,W)) if 0<=yy<pm.height and s[yy*W+x]<120)
        up=dk(ya-1.5); dn=dk(yb+1.5)
        cross=[x for x in up if x in dn]
        if len(cross)>=2: out.append({'ref':ref,'side':side,'src':fn.split('/')[-1],'srcpage':pi+1,'cut_src_y':round(ya,1),'book_pages':[a['page'],b['page']],'crossing_px':len(cross)})
json.dump(out,open('hub/audit/out/page_split.json','w'),indent=0)
from collections import Counter
print(len(out),'page-break splits through ink;',Counter(x['side'] for x in out))
for x in out:
    if x['side']=='Q' or x['crossing_px']>8: print(x)
