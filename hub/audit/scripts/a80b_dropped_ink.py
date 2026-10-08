"""Check 6 (automated part 11): ANY ink dropped by whitespace removal. For every source strip that lies
between two consecutive bands of the same item (and is <=60 pt tall), count dark source pixels that are
not part of a dotted answer line (rows of short, regularly spaced dots) and not page furniture.
Strips that contain text (other sub-parts deliberately left out) are skipped; graphic-only ink there was
removed from the item (lost figure parts, e.g. branches of a skeletal formula, bond lines)."""
import pymupdf as f, json
from collections import defaultdict
o=json.load(open('hub/audit/out/bands.json')); fps=o['fpsrc']; cache={}; rend={}
def page(fn,i):
    if fn not in cache: cache[fn]=f.open(fn)
    return cache[fn][i]
grp=defaultdict(list)
for b in o['bands']:
    m=fps.get(str(b['fp']))
    if m and m['match'] and b['page']!=1273 and b['side']=='Q': grp[(b['ref'],m['match'][0],m['match'][1])].append(b)
Z=150/72; out=[]
def dotted(row):
    runs=[];x=0;n=len(row)
    while x<n:
        if row[x]<120:
            x0=x
            while x<n and row[x]<120: x+=1
            runs.append((x0,x-x0))
        x+=1
    if not runs: return True,0
    short=[r for r in runs if r[1]<=4]
    if len(short)>=15 and len(short)>=0.85*len(runs): return True,0
    return False,sum(r[1] for r in runs)
for (ref,fn,pi),bs in grp.items():
    p=page(fn,pi); H=p.rect.height
    iv=sorted([(H-b['clip'][3],H-b['clip'][1],b['clip'][0],b['clip'][2],b['page']) for b in bs])
    if (fn,pi) not in rend: rend[(fn,pi)]=p.get_pixmap(dpi=150,colorspace=f.csGRAY)
    pm=rend[(fn,pi)]; W=pm.width; s=pm.samples
    for a,b in zip(iv,iv[1:]):
        g0,g1=a[1],b[0]
        if not (0.8<g1-g0<=60): continue
        x0,x1=int(max(a[2],42)*Z),int(min(a[3],553)*Z)
        ink=0; rows=0
        for y in range(int(g0*Z)+1,int(g1*Z)-1):
            row=s[y*W+x0:y*W+min(x1,W)]
            isdot,n=dotted(row)
            if not isdot and n: ink+=n; rows+=1
        words=[w for w in p.get_text('words') if g0+0.5<(w[1]+w[3])/2<g1-0.5 and 42<w[0]<553 and not set(w[4])<=set('.…') and 'UCLES' not in w[4]]
        if ink>=12 and not words:
            out.append({'ref':ref,'src':fn.split('/')[-1],'srcpage':pi+1,'dropped_y':[round(g0,1),round(g1,1)],'ink_px':ink,'rows':rows,'bookpage':b[4]})
json.dump(out,open('hub/audit/out/dropped_ink.json','w'),indent=0)
print(len(out),'strips with dropped ink in',len(set(x['ref'] for x in out)),'items')
for x in sorted(out,key=lambda x:-x['ink_px']): print(x['ref'],'p',x['bookpage'],x['src'],'srcp',x['srcpage'],x['dropped_y'],'ink',x['ink_px'],'rows',x['rows'])
