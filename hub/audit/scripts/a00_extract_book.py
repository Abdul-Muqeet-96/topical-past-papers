"""Audit: dump per-page text (and words) of the final book + unit PDFs to scratch JSON."""
import fitz, json, sys, glob, os
B='Δ-chemistry/booklets/p2-topical-workbook/Chemistry-9701-P2-Topical-Workbook.pdf'
out=sys.argv[1]
d=fitz.open(B)
pages=[]
for p in d:
    pages.append({'text':p.get_text(),'w':p.rect.width,'h':p.rect.height,'imgs':len(p.get_images()),'draw':len(p.get_drawings()) if p.number%1==0 else 0})
json.dump({'pages':pages,'toc':d.get_toc(),'n':len(d)},open(out+'/book_pages.json','w'))
units={}
for f in sorted(glob.glob('Δ-chemistry/booklets/p2-topical-workbook/units/*.pdf')):
    u=fitz.open(f); units[os.path.basename(f)]={'n':len(u),'text':[q.get_text() for q in u],'labels':[q.get_label() for q in u],'toc':u.get_toc()}
json.dump(units,open(out+'/unit_pages.json','w'))
print(len(pages),'book pages;',len(units),'unit pdfs; toc entries',len(d.get_toc()))
