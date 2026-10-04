"""Check 6 (automated part 3): figures/tables cut by a crop edge. For each item+side+source page,
take the union of its band clips; flag source vector paths (lines/curves of diagrams, table
rules) that cross the union's top/bottom edge with >=4pt on each side. Margin furniture
(x<35 or x>560 on portrait pages), page frames and dotted answer lines are ignored."""
import pymupdf as f, json, re
from collections import defaultdict
o=json.load(open('audit/out/bands.json')); fps=o['fpsrc']
cache={}; dcache={}
def page(fn,i):
    if fn not in cache: cache[fn]=f.open(fn)
    return cache[fn][i]
def drawings(fn,i):
    k=(fn,i)
    if k not in dcache:
        p=page(fn,i); RM=p.rotation_matrix
        dcache[k]=[(dd['rect']*RM, dd.get('width') or 0, len(dd['items'])) for dd in p.get_drawings() if (dd.get('fill_opacity') in (None,1) and dd.get('stroke_opacity') in (None,1))]
    return dcache[k]
grp=defaultdict(list)
for b in o['bands']:
    m=fps.get(str(b['fp']))
    if not m or not m['match'] or b['page']==1273: continue
    grp[(b['ref'],b['side'],m['match'][0],m['match'][1])].append(b)
out=[]
for (ref,side,fn,pi),bs in grp.items():
    p=page(fn,pi); Hh=p.rect.height; Wd=p.rect.width
    cl=sorted([f.Rect(c[0],Hh-c[3],c[2],Hh-c[1]) for c in [b['clip'] for b in bs]],key=lambda r:r.y0)
    # merge contiguous clips into intervals
    iv=[]
    for c in cl:
        if iv and c.y0<=iv[-1][1]+1.5: iv[-1][1]=max(iv[-1][1],c.y1)
        else: iv.append([c.y0,c.y1])
    for r,w,n in drawings(fn,pi):
        if r.width>Wd*0.9 and r.height>Hh*0.5: continue
        if Wd<700 and (r.x1<35 or r.x0>560): continue
        if r.height<1 and r.width>200: continue   # long horizontal rule (answer line / table rule)
        for a,b in iv:
            for edge in (a,b):
                if r.y0<edge-4 and r.y1>edge+4 and (r.y1>a and r.y0<b):
                    out.append({'ref':ref,'side':side,'src':fn.split('/')[-1],'srcpage':pi+1,'edge':round(edge,1),'path':[round(x) for x in r],'bookpages':sorted(set(b2['page'] for b2 in bs))})
# collapse to one row per item/side/src page/edge
seen={}
for x in out: seen.setdefault((x['ref'],x['side'],x['src'],x['srcpage'],x['edge']),x)
rows=list(seen.values())
json.dump(rows,open('audit/out/cutfigs.json','w'),indent=0)
from collections import Counter
print('edges cutting vector paths',len(rows),'items/answers',len(set((x['ref'],x['side']) for x in rows)),Counter(x['side'] for x in rows))
for x in rows[:40]: print(x['ref'],x['side'],x['src'],x['srcpage'],x['edge'],x['path'],x['bookpages'])
