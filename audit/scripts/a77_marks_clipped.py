"""Check 6 (automated part 8): mark brackets '[n]' whose glyph box is cut by the bottom/top of a crop
(3-97% of the box inside the crop union), i.e. visibly truncated marks."""
import pymupdf as f, json, re
from collections import defaultdict
o=json.load(open('audit/out/bands.json')); fps=o['fpsrc']; cache={}
def page(fn,i):
    if fn not in cache: cache[fn]=f.open(fn)
    return cache[fn][i]
grp=defaultdict(list)
for b in o['bands']:
    m=fps.get(str(b['fp']))
    if m and m['match'] and b['side']=='Q': grp[(b['ref'],m['match'][0],m['match'][1])].append(b)
out=[]
for (ref,fn,pi),bs in grp.items():
    p=page(fn,pi); H=p.rect.height; RM=p.rotation_matrix
    cl=[f.Rect(c[0],H-c[3],c[2],H-c[1]) for c in [b['clip'] for b in bs]]
    for w in p.get_text('words'):
        if not re.fullmatch(r'\[\d{1,2}\]|\[Total:|\d{1,2}\]',w[4]): continue
        r=f.Rect(w[:4])*RM
        ins=sum(max(0,min(r.y1,c.y1)-max(r.y0,c.y0)) for c in cl if r.x0<c.x1 and r.x1>c.x0)/r.height
        if 0.03<ins<0.97: out.append({'ref':ref,'src':fn.split('/')[-1],'srcpage':pi+1,'word':w[4],'inside':round(ins,2),'bookpages':sorted(set(b['page'] for b in bs))})
json.dump(out,open('audit/out/marks_clipped.json','w'),indent=0)
print(len(out),'cut mark brackets in',len(set(x['ref'] for x in out)),'items')
for x in out: print(x)
