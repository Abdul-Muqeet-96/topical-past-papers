"""Check 6 (automated part 4): page furniture inside crops. For every band, does its clip reach into
the source page's header/footer zone where the page number, barcode, corner marks, '© UCLES' footer,
'[Turn over' and the download-site logo sit? Zone found per source page from the actual furniture
text positions (page number / UCLES / Turn over), so scaled pages (m20) are handled. Also scans
rendered book pages for the red PapaCambridge logo."""
import pymupdf as f, json, re
from collections import defaultdict
o=json.load(open('hub/audit/out/bands.json')); fps=o['fpsrc']
cache={}; zc={}
def zones(fn,i):
    if (fn,i) in zc: return zc[(fn,i)]
    if fn not in cache: cache[fn]=f.open(fn)
    p=cache[fn][i]; RM=p.rotation_matrix; H=p.rect.height
    top=None; bot=None
    for w in p.get_text('words'):
        r=f.Rect(w[:4])*RM
        if r.y1<H*0.075 and re.fullmatch(r'\d{1,2}',w[4]) and abs((r.x0+r.x1)/2-p.rect.width/2)<25: top=max(top or 0,r.y1)
        if r.y0>H*0.85 and ('UCLES' in w[4] or 'Turn' in w[4] or re.match(r'9701/\d\d/',w[4]) or w[4]=='Cambridge' and r.y0>H*0.9): bot=min(bot or H,r.y0)
    zc[(fn,i)]=(top,bot,H); return zc[(fn,i)]
hits=defaultdict(set)
for b in o['bands']:
    m=fps.get(str(b['fp']))
    if not m or not m['match'] or b['page']==1273: continue
    fn,pi=m['match']; top,bot,H=zones(fn,pi)
    c=b['clip']; y0,y1=H-c[3],H-c[1]
    if top is not None and y0<top-2: hits[(b['ref'],b['side'],b['page'])].add('top furniture (page number / barcode zone)')
    if bot is not None and y1>bot+2: hits[(b['ref'],b['side'],b['page'])].add('footer zone (UCLES / Turn over / paper code)')
rows=[{'ref':k[0],'side':k[1],'page':k[2],'what':sorted(v)} for k,v in hits.items()]
# logo scan (rendered pixels)
d=f.open('Δ-chemistry/booklets/p2-topical-workbook/Chemistry-9701-P2-Topical-Workbook.pdf'); logo=[]
for i in range(len(d)):
    pm=d[i].get_pixmap(dpi=36); s=pm.samples; n=0
    for j in range(0,len(s),3):
        if s[j]>170 and s[j+1]<90 and s[j+2]<90: n+=1
    if n>15: logo.append((i+1,n))
json.dump({'furniture':rows,'logo_pages':logo},open('hub/audit/out/furniture.json','w'),indent=0)
from collections import Counter
print('bands reaching furniture zones:',len(rows),Counter(tuple(r['what']) for r in rows)); print('pages with red logo pixels',logo)
for r in rows[:30]: print(r)
