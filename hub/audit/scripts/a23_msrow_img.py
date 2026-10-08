"""Audit helper: render the MS page region around a row label (visual evidence)."""
import pymupdf as f, sys
sys.path.insert(0,'hub/audit/scripts'); from a03_lines import lines
fn,label,out=sys.argv[1],sys.argv[2],sys.argv[3]; h=float(sys.argv[4]) if len(sys.argv)>4 else 160
d=f.open(fn)
for i,p in enumerate(d):
    for l in lines(p,merge=True):
        if l['w'] and l['w'][0][0]<130 and ''.join(w[4] for w in l['w'][:2]).replace(' ','').startswith(label):
            from PIL import Image
            z=float(sys.argv[5]) if len(sys.argv)>5 else 1.0
            pm=p.get_pixmap(matrix=f.Matrix(z,z)); im=Image.frombytes('RGB',(pm.width,pm.height),pm.samples)
            im.crop((int(40*z),int((l['c']-14)*z),int(min(pm.width/z,830)*z),int(min(l['c']+h,pm.height/z)*z))).save(out); print('page',i+1,'y',round(l['c'])); sys.exit()
print('not found')
