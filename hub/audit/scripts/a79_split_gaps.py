"""Check 6 (automated part 10): figures broken by whitespace removal. Between consecutive bands of the
same item and source page, the build drops source rows it judged empty. If a dropped strip (<=40 pt)
contains a vertical line that runs through >=70% of the strip's height (a bond, axis, arrow or box edge
crossing it), that line is cut and the figure shows a white break. Checked on the source rendered at
150 dpi, inside the band's x-range only (margin text excluded), ignoring the light watermark."""
import pymupdf as f, json
from collections import defaultdict
o=json.load(open('hub/audit/out/bands.json')); fps=o['fpsrc']; cache={}; rend={}
def page(fn,i):
    if fn not in cache: cache[fn]=f.open(fn)
    return cache[fn][i]
grp=defaultdict(list)
for b in o['bands']:
    m=fps.get(str(b['fp']))
    if m and m['match'] and b['page']!=1273: grp[(b['ref'],b['side'],m['match'][0],m['match'][1])].append(b)
Z=150/72; out=[]
for (ref,side,fn,pi),bs in grp.items():
    p=page(fn,pi); H=p.rect.height
    iv=sorted([(H-b['clip'][3],H-b['clip'][1],b['clip'][0],b['clip'][2],b['page']) for b in bs])
    if (fn,pi) not in rend: rend[(fn,pi)]=p.get_pixmap(dpi=150,colorspace=f.csGRAY)
    pm=rend[(fn,pi)]; W=pm.width; s=pm.samples
    for a,b in zip(iv,iv[1:]):
        g0,g1=a[1],b[0]
        if not (0.8<g1-g0<=40): continue
        y0,y1=int(g0*Z)+1,int(g1*Z)-1
        if y1-y0<2: continue
        x0,x1=int(max(a[2],38)*Z),int(min(a[3],557)*Z)
        cols=0; xs=[]
        for x in range(x0,min(x1,W)):
            n=sum(1 for y in range(y0,y1) if s[y*W+x]<120)
            if n>=0.7*(y1-y0): cols+=1; xs.append(x)
        # group adjacent columns into lines
        lines=[]; 
        for x in xs:
            if lines and x-lines[-1][-1]<=1: lines[-1].append(x)
            else: lines.append([x])
        lines=[l for l in lines if len(l)<=6]   # thin vertical strokes only (not filled boxes)
        if lines:
            out.append({'ref':ref,'side':side,'src':fn.split('/')[-1],'srcpage':pi+1,'dropped_y':[round(g0,1),round(g1,1)],'vertical_lines_cut':len(lines),'bookpage':b[4]})
json.dump(out,open('hub/audit/out/split_gaps.json','w'),indent=0)
from collections import Counter
items=sorted(set((x['ref'],x['side']) for x in out))
print(len(out),'dropped strips cutting vertical lines in',len(items),'items/answers',Counter(s for _,s in items))
for x in out:
    if x['side']=='Q': print(x['ref'],x['bookpage'],x['src'],x['srcpage'],x['dropped_y'],x['vertical_lines_cut'])
