"""Check 6 (automated part 12): figure/axis text cut off at the LEFT/RIGHT crop edge. Source words that
sit vertically inside an item's band but horizontally entirely outside it (left of clip x0 or right of
clip x1), excluding margin furniture ('DO NOT WRITE IN THIS MARGIN', barcodes, page numbers)."""
import pymupdf as f, json, re
from collections import defaultdict
o=json.load(open('audit/out/bands.json')); fps=o['fpsrc']; cache={}
def page(fn,i):
    if fn not in cache: cache[fn]=f.open(fn)
    return cache[fn][i]
grp=defaultdict(list)
for b in o['bands']:
    m=fps.get(str(b['fp']))
    if m and m['match'] and b['page']!=1273: grp[(b['ref'],b['side'],m['match'][0],m['match'][1])].append(b)
MARG={'DO','NOT','WRITE','IN','THIS','MARGIN'}
out=[]
for (ref,side,fn,pi),bs in grp.items():
    p=page(fn,pi); H=p.rect.height; RM=p.rotation_matrix; Wd=p.rect.width
    ws=[(f.Rect(w[:4])*RM,w[4]) for w in p.get_text('words')]
    for b in bs:
        c=b['clip']; cy0,cy1=H-c[3],H-c[1]
        for r,t in ws:
            cy=(r.y0+r.y1)/2
            if not (cy0<cy<cy1): continue
            if (r.x1<=c[0]+0.5 or r.x0>=c[2]-0.5):
                if t in MARG or re.fullmatch(r'[*\d]+',t) or r.x1<12 or r.x0>Wd-12: continue
                out.append({'ref':ref,'side':side,'src':fn.split('/')[-1],'srcpage':pi+1,'word':t,'x':round(r.x0),'clip_x':[round(c[0]),round(c[2])],'bookpage':b['page']})
json.dump(out,open('audit/out/side_cut.json','w'),indent=0)
from collections import Counter
print(len(out),'words cut at left/right in',len(set((x['ref'],x['side']) for x in out)),'items/answers',Counter(x['side'] for x in out))
seen=set()
for x in out:
    k=(x['ref'],x['side'])
    if k in seen: continue
    seen.add(k); print(x['ref'],x['side'],'p',x['bookpage'],x['src'],[y['word'] for y in out if (y['ref'],y['side'])==k][:8])
