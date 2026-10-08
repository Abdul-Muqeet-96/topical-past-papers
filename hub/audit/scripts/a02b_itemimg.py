"""Audit helper: render one item (question or answer side) region from the book: from its heading to
the next heading (or page end). usage: ref side out.png dpi"""
import sys, json, pymupdf as f
from PIL import Image
ref,side,out=sys.argv[1],sys.argv[2],sys.argv[3]; dpi=int(sys.argv[4]) if len(sys.argv)>4 else 70
bi=sorted(json.load(open('hub/audit/out/book_items.json')),key=lambda i:(i['page'],i['y']))
d=f.open('Δ-chemistry/booklets/p2-topical-workbook/Chemistry-9701-P2-Topical-Workbook.pdf')
k=[n for n,i in enumerate(bi) if i['ref']==ref and i['side']==side][0]; a=bi[k]; b=bi[k+1] if k+1<len(bi) else None
ims=[]; z=dpi/72
for pg in range(a['page'], (b['page'] if b else a['page'])+1):
    p=d[pg-1]; y0=a['y']-10 if pg==a['page'] else 48; y1=(b['y']-12) if (b and pg==b['page']) else 800
    if y1-y0<5: continue
    pm=p.get_pixmap(dpi=dpi,clip=f.Rect(30,y0,565,y1)); ims.append(Image.frombytes('RGB',(pm.width,pm.height),pm.samples))
W=max(i.width for i in ims); H=sum(i.height for i in ims)+4*len(ims)
S=Image.new('RGB',(W,H),'red'); y=0
for i in ims: S.paste(i,(0,y)); y+=i.height+4
S.save(out)
