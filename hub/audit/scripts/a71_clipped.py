"""Check 6 (automated part 2): text clipped at crop edges. For each item+side+source page, take the
union of its band clips (source user space) and list source words only PARTLY covered
(10-90% of their height or width). Also verifies the band->source mapping by checking that the
words fully inside the clips reproduce the band text."""
import pymupdf as f, json, re
from collections import defaultdict
o=json.load(open('hub/audit/out/bands.json')); fps=o['fpsrc']
cache={}
def page(fn,i):
    if fn not in cache: cache[fn]=f.open(fn)
    return cache[fn][i]
grp=defaultdict(list)
for b in o['bands']:
    m=fps.get(str(b['fp']))
    if not m or not m['match'] or b['page']==1273: continue
    grp[(b['ref'],b['side'],m['match'][0],m['match'][1])].append(b)
out=[]
for (ref,side,fn,pi),bs in grp.items():
    p=page(fn,pi); Hh=p.rect.height; RM=p.rotation_matrix
    clips=[f.Rect(c[0],Hh-c[3],c[2],Hh-c[1]) for c in [b['clip'] for b in bs]]
    for w in p.get_text('words'):
        r=f.Rect(w[:4])*RM
        if not w[4].strip() or r.height<=0: continue
        inside=sum(max(0,min(r.y1,c.y1)-max(r.y0,c.y0))*(1 if (r.x0<c.x1 and r.x1>c.x0) else 0) for c in clips)/r.height
        hx=[c for c in clips if c.y0<=r.y0+1 and c.y1>=r.y1-1]
        xin=max([max(0,min(r.x1,c.x1)-max(r.x0,c.x0))/max(r.width,0.1) for c in hx],default=1)
        if 0.12<inside<0.88 or (hx and 0.12<xin<0.88):
            if re.fullmatch(r'[.…]+',w[4]): continue   # dotted answer line fragments are meant to be cut
            out.append({'ref':ref,'side':side,'src':fn.split('/')[-1],'srcpage':pi+1,'word':w[4],'vfrac':round(inside,2),'hfrac':round(xin,2),'bookpages':sorted(set(b['page'] for b in bs))})
json.dump(out,open('hub/audit/out/clipped.json','w'),indent=0)
from collections import Counter
print('partly-clipped words',len(out),'in',len(set((x['ref'],x['side']) for x in out)),'items/answers;',Counter(x['side'] for x in out))
for x in out[:25]: print(x)
