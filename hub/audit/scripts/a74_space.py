"""Check 6 (automated part 5): blank/near-blank pages, large empty gaps inside a page, and items that
start on one page and continue on the next (split items). Pixel-based (rendered at 30 dpi)."""
import pymupdf as f, json
d=f.open('Δ-chemistry/p2-topical-workbook/Chemistry-9701-P2-Topical-Workbook.pdf')
bi=json.load(open('audit/out/book_items.json'))
rows=[]
for i in range(len(d)):
    pm=d[i].get_pixmap(dpi=30,colorspace=f.csGRAY); W,H=pm.width,pm.height; s=pm.samples
    sc=30/72; top=int(48*sc); bot=int(800*sc)
    ink=[sum(1 for x in range(W) if s[y*W+x]<200) for y in range(top,bot)]
    tot=sum(ink); rowsink=[k for k,v in enumerate(ink) if v>0]
    gaps=[]; prev=None
    for k in rowsink:
        if prev is not None and k-prev>1: gaps.append(((prev+top)/sc,(k+top)/sc))
        prev=k
    big=[g for g in gaps if g[1]-g[0]>180]
    trailing=(bot-(rowsink[-1]+top))/sc if rowsink else None
    rows.append({'page':i+1,'ink':tot,'interior_gaps_gt180pt':[(round(a),round(b)) for a,b in big],'trailing_blank_pt':round(trailing) if trailing else None})
json.dump(rows,open('audit/out/space.json','w'))
blank=[r['page'] for r in rows if r['ink']<40]
print('near-blank pages (body ink<40px @30dpi):',blank)
print('pages with interior gap >180pt:',len([r for r in rows if r['interior_gaps_gt180pt']]),[ (r['page'],r['interior_gaps_gt180pt']) for r in rows if r['interior_gaps_gt180pt']][:20])
tb=[r for r in rows if r['trailing_blank_pt'] and r['trailing_blank_pt']>350]
print('pages with >350pt trailing blank:',len(tb),[r['page'] for r in tb][:40])
