"""Check 6 visual: contact sheets of sampled items (15 question items + 5 answers per unit, evenly
spaced through the unit) for eye review. Each tile = the item region rendered from the book."""
import json, sys, pymupdf as f
from PIL import Image, ImageDraw
out=sys.argv[1]
bi=sorted(json.load(open('audit/out/book_items.json')),key=lambda i:(i['page'],i['y']))
d=f.open('Δ-chemistry/p2-topical-workbook/Chemistry-9701-P2-Topical-Workbook.pdf')
def tile(k,dpi=48,maxh=720):
    a=bi[k]; b=bi[k+1] if k+1<len(bi) else None; ims=[]
    for pg in range(a['page'],(b['page'] if b else a['page'])+1):
        y0=a['y']-10 if pg==a['page'] else 48; y1=(b['y']-12) if (b and pg==b['page']) else 805
        if y1-y0<5: continue
        pm=d[pg-1].get_pixmap(dpi=dpi,clip=f.Rect(30,y0,565,y1)); ims.append(Image.frombytes('RGB',(pm.width,pm.height),pm.samples))
    W=max(i.width for i in ims); H=sum(i.height+3 for i in ims); T=Image.new('RGB',(W,H),(200,0,0)); y=0
    for i in ims: T.paste(i,(0,y)); y+=i.height+3
    if T.height>maxh: T=T.crop((0,0,W,maxh))
    return T
sample=[]
for u in range(1,23):
    for side,n in (('Q',15),('A',5)):
        ks=[k for k,i in enumerate(bi) if i['unit']==u and i['side']==side]
        step=len(ks)/n; pick=[ks[int(j*step)] for j in range(n)]
        sample+= [(u,side,k) for k in pick]
json.dump([(u,s,bi[k]['ref'],bi[k]['page']) for u,s,k in sample],open('audit/out/visual_sample.json','w'))
per=6; n=0
for s in range(0,len(sample),per):
    tiles=[tile(k) for _,_,k in sample[s:s+per]]
    W=max(t.width for t in tiles); H=max(t.height for t in tiles)
    sheet=Image.new('RGB',(W*3+20,H*2+10),'white')
    for j,t in enumerate(tiles): sheet.paste(t,((j%3)*(W+10),(j//3)*(H+10)))
    sheet.save(f'{out}/sheet_{n:03d}.png'); n+=1
print(len(sample),'items sampled;',n,'sheets')
