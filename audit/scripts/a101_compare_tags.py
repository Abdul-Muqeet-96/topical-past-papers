"""Check 8: compare my blind re-tags (audit/out/my_tags.txt) with the build's unit per item."""
import json, csv, re
from collections import Counter
own=json.load(open('audit/out/owntext.json'))
idx={r['reference']:r for r in csv.DictReader(open('Δ-chemistry/p2-topical-workbook/index.csv'))}
tags={}
for l in open('audit/out/my_tags.txt'):
    if l.startswith('#') or not l.strip(): continue
    i,t=l.strip().split(':',1); tags[int(i)]=t
rows=[]; c=Counter()
for i,o in enumerate(own):
    t=tags.get(i); u=int(idx[o['ref']]['unit'])
    if t is None or t.startswith('?'): st='not judged'
    else:
        s=[int(x) for x in t.split('/') if x.isdigit()]
        st='agree (first choice)' if s[0]==u else 'agree (alternative)' if u in s else 'DISAGREE'
    c[st]+=1; rows.append({'i':i,'ref':o['ref'],'build_unit':u,'my':t,'status':st,'page':idx[o['ref']]['page'],'also':idx[o['ref']]['also_topics']})
json.dump(rows,open('audit/out/tag_compare.json','w'),indent=0)
print(dict(c),'of',len(own))
for r in rows:
    if r['status']=='DISAGREE': print(r['i'],r['ref'],'build',r['build_unit'],'me',r['my'],'p',r['page'])
