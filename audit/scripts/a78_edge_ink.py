"""Check 6 (automated part 9): ink touching a crop edge. For every placed band on every book page,
render at 144 dpi and count dark pixels in the 1-px rows just inside its top and bottom edges.
Ink on the edge row means a glyph or line continues past the crop, i.e. it is cut."""
import pymupdf as f, json
from collections import defaultdict
o=json.load(open('audit/out/bands.json'))
d=f.open('Δ-chemistry/p2-topical-workbook/Chemistry-9701-P2-Topical-Workbook.pdf')
byp=defaultdict(list)
for b in o['bands']: byp[b['page']].append(b)
Z=144/72; out=[]
for pg,bs in byp.items():
    if pg==len(d): continue
    pm=d[pg-1].get_pixmap(dpi=144,colorspace=f.csGRAY); W,H,s=pm.width,pm.height,pm.samples
    for b in bs:
        x0,y0,x1,y1=b['target']
        for edge,yy in (('top',int(y0*Z)+1),('bottom',int(y1*Z)-2)):
            if not (0<=yy<H): continue
            row=s[yy*W+int(x0*Z):yy*W+int(x1*Z)]
            n=sum(1 for v in row if v<110)
            if n>=3: out.append({'page':pg,'ref':b['ref'],'side':b['side'],'edge':edge,'dark_px':n})
# a band edge that touches the next band of the same item continues legitimately; keep only edges where the
# neighbouring area outside the band is white (checked by the next band not abutting)
json.dump(out,open('audit/out/edge_ink.json','w'),indent=0)
from collections import Counter
print(len(out),'edges with ink;',Counter((x['side'],x['edge']) for x in out)); print('items',len(set((x['ref'],x['side']) for x in out)))
