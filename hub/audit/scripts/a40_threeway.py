"""Check 4 THREE-WAY: book (question side) vs index.csv vs work/items_phase*.json (no items.jsonl
exists) vs per-unit PDFs: same items, same units, same order, same pages. Also A-side vs Q-side."""
import json, csv, glob, os, re, sys
sys.path.insert(0,'audit/scripts'); from a30_book_items import parse
from collections import Counter
bi=json.load(open('audit/out/book_items.json'))
Q=[i for i in bi if i['side']=='Q']; A=[i for i in bi if i['side']=='A']
idx=list(csv.DictReader(open('Δ-chemistry/p2-topical-workbook/index.csv')))
js=json.load(open('Δ-chemistry/work/items_phase1.json'))+json.load(open('Δ-chemistry/work/items_phase2.json'))
F=[]
def fail(kind,ref,page,detail): F.append({'kind':kind,'ref':ref,'page':page,'detail':detail})
# A: book Q vs index.csv
bq={i['ref']:i for i in Q}
if len(bq)!=len(Q): fail('dup-ref-in-book',None,None,[r for r,c in Counter(i['ref'] for i in Q).items() if c>1])
ix={r['reference']:r for r in idx}
for r in set(bq)-set(ix): fail('in-book-not-index',r,bq[r]['page'],'')
for r in set(ix)-set(bq): fail('in-index-not-book',r,ix[r]['page'],'')
for r in set(bq)&set(ix):
    if int(ix[r]['unit'])!=bq[r]['unit']: fail('unit-mismatch book/index',r,bq[r]['page'],f"book {bq[r]['unit']} index {ix[r]['unit']}")
    if int(ix[r]['page'])!=bq[r]['page']: fail('page-mismatch book/index',r,bq[r]['page'],f"index {ix[r]['page']}")
# order: index rows grouped by unit in book order?
order_book=[i['ref'] for i in sorted(Q,key=lambda i:(i['page'],i['y']))]
order_idx=[r['reference'] for r in sorted(idx,key=lambda r:(int(r['unit']),int(r['page'])))]
print('index.csv row order == book order:',[r['reference'] for r in idx]==order_book,'; sorted-by-unit/page index == book order:',order_idx==order_book)
# B: book vs items json
jr={}
for it in js: jr.setdefault(it['ref'],[]).append(it)
for r in set(bq)-set(jr): fail('in-book-not-items.json',r,bq[r]['page'],'')
for r in set(jr)-set(bq): fail('in-items.json-not-book',r,None,'')
for r in set(bq)&set(jr):
    if jr[r][0]['topic']!=bq[r]['unit']: fail('unit-mismatch book/items.json',r,bq[r]['page'],f"json {jr[r][0]['topic']}")
# C: numbering sequential per unit; answers same numbers/refs/order
for u in range(1,23):
    q=[i for i in sorted(Q,key=lambda i:(i['page'],i['y'])) if i['unit']==u]
    a=[i for i in sorted(A,key=lambda i:(i['page'],i['y'])) if i['unit']==u]
    if [i['n'] for i in q]!=list(range(1,len(q)+1)): fail('numbering-not-sequential',f'unit {u}',None,'')
    if [(i['n'],i['ref']) for i in q]!=[(i['n'],i['ref']) for i in a]: fail('answers!=questions order/number',f'unit {u}',None,'')
# D: unit PDFs
for fn in sorted(glob.glob('Δ-chemistry/p2-topical-workbook/units/*.pdf')):
    u=int(re.search(r'Unit-(\d+)',fn).group(1)); o=parse(fn)
    up=[i for i in o['items']]
    qb=[i for i in sorted(bi,key=lambda i:(i['page'],i['y'])) if i['unit']==u]
    a=[(i['n'],i['ref']) for i in up]; b=[(i['n'],i['ref']) for i in qb]
    if a!=b: fail('unit-pdf items/order differ from book',f'unit {u}',None,f'{len(a)} vs {len(b)}')
    # page labels in unit PDF should equal book page numbers
    labs=[p['label'] for p in o['pages']]
    bp=sorted(set(i['page'] for i in qb)); 
    upages=[p for p in o['pages']]
    mism=0
    for i,j in zip(up,qb):
        lab=o['pages'][i['page']-1]['label']; hdr=' '.join(o['pages'][i['page']-1]['header'])
        num=re.search(r'Workbook (\d+)',hdr)
        if not (lab==str(j['page']) or (num and int(num.group(1))==j['page'])): mism+=1
    if mism: fail('unit-pdf printed page != book page',f'unit {u}',None,f'{mism} items')
json.dump(F,open('audit/out/threeway_fail.json','w'),indent=0)
print('Q items',len(Q),'A items',len(A),'index rows',len(idx),'items.json',len(js)); print(Counter(f['kind'] for f in F))
for f in F[:15]: print(f)
