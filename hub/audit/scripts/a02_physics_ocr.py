"""Audit: OCR the left reference column of the scanned Physics booklet (tesseract) and list item
reference lines, to find partial items (references with part letters)."""
import pymupdf as f, subprocess, re, json, sys, os
from concurrent.futures import ThreadPoolExecutor
S=sys.argv[1]; d=f.open('Ω-physics/reference/Physics paper 2 9702 3.pdf')
fns=[]
for i in range(len(d)):
    fn=f'{S}/phocr_{i}.png'; d[i].get_pixmap(dpi=120,clip=f.Rect(30,40,330,830),colorspace=f.csGRAY).save(fn); fns.append(fn)
def run(fn): return subprocess.run(['tesseract',fn,'-','--psm','6'],capture_output=True,text=True).stdout
with ThreadPoolExecutor(os.cpu_count() or 4) as ex: txt=list(ex.map(run,fns))
for fn in fns: os.remove(fn)
json.dump(txt,open(f'{S}/physics_ocr.json','w'))
refs=[]
for i,t in enumerate(txt):
    for m in re.finditer(r'(\d+)\s*[.,]\s*((?:M/?J|O/?N|MAR|F/?M)\s*\d\d\s*/\s*P\s*\d\d\s*/\s*Q\s*\d+\S*)',t):
        refs.append((i+1,m.group(1),m.group(2)))
json.dump(refs,open(f'{S}/physics_refs.json','w'))
part=[r for r in refs if re.search(r'Q\s*\d+\s*[/,]',r[2])]
print(len(refs),'refs;',len(part),'partial')
for r in part: print(r)
