"""Check 9 BOOK STRUCTURE: contents vs real pages, running headers, page numbering, branding,
newest-first order, bookmarks, Periodic Table appendix."""
import json, re, pymupdf as f, sys
B='Δ-chemistry/booklets/p2-topical-workbook/Chemistry-9701-P2-Topical-Workbook.pdf'
d=f.open(B); bp=json.load(open('hub/audit/out/book_parse.json')); bi=json.load(open('hub/audit/out/book_items.json'))
F=[]; info={}
# contents
ct=d[1].get_text()+d[2].get_text()
ents=re.findall(r'^(.+?) \.{3,} (\d+)$',ct,re.M); info['contents_entries']=len(ents)
units=[p['i'] for p in bp['pages'] if 'unit_title' in p]; ans=[p['i'] for p in bp['pages'] if p.get('answers_banner')]
names=[]
k=0
for name,pg in ents:
    pg=int(pg)
    if name=='Answers Section': exp=ans[k-1] if k-1<len(ans) else None
    elif name in ('Topic index','The Periodic Table of Elements'):
        exp=next((i+1 for i in range(len(d)) if (name=='Topic index' and 'Topic index: where each part was filed' in d[i].get_text()) or (name!='Topic index' and 'APPENDIX' not in d[i].get_text()[:5] and i+1>ans[-1] and 'Periodic' in d[i].get_text() )),None)
    else: exp=units[k] if k<len(units) else None; names.append(name); k+=1
    if exp!=pg: F.append(('contents-page-wrong',name,pg,exp))
info['unit_names']=names
# running header and page numbers
uname={i+1:n for i,n in enumerate(names)}
bad_hdr=[]; bad_num=[]
def unit_of(pg):
    u=None
    for i,s in enumerate(units):
        if pg>=s: u=i+1
    return u
for p in bp['pages']:
    i=p['i']; h=' '.join(p['header'])
    if i<=3 or 'unit_title' in p: continue
    u=unit_of(i)
    m=re.search(r'Workbook (\d+)',h)
    if not m or int(m.group(1))!=i: bad_num.append(i)
    if u and i< (bp['pages'][-1]['i']) and i<next((x['i'] for x in bp['pages'] if 'Topic index' in ' '.join(x['header'])),10**9):
        isA=any(a<=i<(units[j+1] if j+1<len(units) else 10**9) for j,a in enumerate(ans) if j+1==u)
        want=f"Unit {u}: Answers Section" if isA else f"Unit {u}: {uname.get(u)}"
        if want not in h: bad_hdr.append((i,h[-60:],want))
info['pages_with_bad_header']=len(bad_hdr); info['bad_header_examples']=bad_hdr[:8]
info['pages_with_bad_number']=len(bad_num); info['bad_number_examples']=bad_num[:10]
info['page_labels_set']=any(p['label'] for p in bp['pages'])
info['toc_entries']=len(d.get_toc())
info['branding_hits']=[i+1 for i in range(len(d)) if re.search(r'Read\s*(&|and)\s*Write|R&W',d[i].get_text(),re.I)]
# newest-first: derive sort key from reference
def key(ref):
    m=re.match(r'(M/J|O/N|MAR) (\d\d)/P(\d\d)/Q(\d+)(.*)',ref); s={'MAR':0,'M/J':1,'O/N':2}[m.group(1)]
    return (int(m.group(2)),s)
order_bad=[]
for u in range(1,23):
    q=[i for i in sorted(bi,key=lambda i:(i['page'],i['y'])) if i['unit']==u and i['side']=='Q']
    for a,b in zip(q,q[1:]):
        if key(a['ref'])<key(b['ref']): order_bad.append((u,a['ref'],b['ref'],b['page']))
info['newest_first_violations']=len(order_bad); info['order_examples']=order_bad[:10]
last=d[-1].get_text(); info['last_page_head']=last[:200]
info['contents_fail']=F
json.dump(info,open('hub/audit/out/structure.json','w'),indent=1)
for k,v in info.items(): print(k,':',str(v)[:400])
