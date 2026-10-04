"""Check 6 (automated part 6): leftover dotted answer lines that are still VISIBLE. The build hides
answer lines with white rectangles, so the dots stay in the text layer; a dot-run word is
'visible' if the rendered pixels inside its box contain ink."""
import pymupdf as f, json, re
d=f.open('Δ-chemistry/p2-topical-workbook/Chemistry-9701-P2-Topical-Workbook.pdf')
bi=json.load(open('audit/out/book_items.json')); seq=sorted(bi,key=lambda i:(i['page'],i['y']))
import bisect; keys=[(i['page'],i['y']) for i in seq]
vis=[]; hidden=0
Z=100/72
for i in range(len(d)):
    p=d[i]; ws=[w for w in p.get_text('words') if re.fullmatch(r'[.…]{6,}.*|.*[.…]{8,}',w[4])]
    if not ws: continue
    pm=p.get_pixmap(dpi=100,colorspace=f.csGRAY); W=pm.width; s=pm.samples
    for w in ws:
        x0,y0,x1,y1=[int(v*Z) for v in w[:4]]
        dark=sum(1 for y in range(max(0,y0),min(pm.height,y1)) for x in range(max(0,x0),min(W,x1)) if s[y*W+x]<160)
        area=max(1,(x1-x0)*(y1-y0))
        if dark/area>0.02:
            k=bisect.bisect_right(keys,(i+1,w[1]))-1
            vis.append({'page':i+1,'ref':seq[k]['ref'] if k>=0 else None,'side':seq[k]['side'] if k>=0 else None,'word':w[4][:30],'ink':round(dark/area,3)})
        else: hidden+=1
json.dump(vis,open('audit/out/dots_visible.json','w'),indent=0)
from collections import Counter
print('dot runs hidden',hidden,'; visible',len(vis),Counter(v['side'] for v in vis)); 
for v in vis[:20]: print(v)
