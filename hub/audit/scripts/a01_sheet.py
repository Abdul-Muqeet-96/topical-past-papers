"""Audit helper: contact sheet of PDF pages. usage: a01_sheet.py pdf out.png dpi cols p1 p2 ... (1-based)"""
import sys, pymupdf as f
from PIL import Image
pdf,out,dpi,cols=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]); ps=[int(x) for x in sys.argv[5:]]
d=f.open(pdf); ims=[]
for p in ps:
    pm=d[p-1].get_pixmap(dpi=dpi); ims.append(Image.frombytes('RGB',(pm.width,pm.height),pm.samples))
w,h=max(i.width for i in ims),max(i.height for i in ims); rows=(len(ims)+cols-1)//cols
S=Image.new('RGB',(w*cols,h*rows),'white')
for k,i in enumerate(ims): S.paste(i,((k%cols)*w,(k//cols)*h))
S.save(out)
