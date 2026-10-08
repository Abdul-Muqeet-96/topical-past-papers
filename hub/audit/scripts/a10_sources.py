"""Check 1 SOURCE: expected paper list (from CLAUDE.md rules), presence in data/, page-1 header
parsed independently (code 9701/vv, 'Paper 2', series text), qp vs ms type."""
import pymupdf as f, os, re, json, sys
def expected():
    E=[]
    for y in range(16,27): E.append(('m',y,22))
    for y in range(15,27):
        for v in (21,22,23): E.append(('s',y,v))
    for y in range(15,26):
        for v in (21,22,23): E.append(('w',y,v))
    for s,y in (('s',25),('s',26),('w',25)): E.append((s,y,24))
    return E
SER={'m':('February/March','March'),'s':('May/June',),'w':('October/November',)}
rows=[]
for s,y,v in expected():
    for t in ('qp','ms'):
        fn=f'hub/data/9701_{s}{y}_{t}_{v}.pdf'; r={'file':fn,'series':s,'year':y,'variant':v,'type':t,'phase':1 if (y>22 or (y==22)) else 2}
        if not os.path.exists(fn): r['status']='MISSING'; rows.append(r); continue
        try: d=f.open(fn)
        except Exception as e: r['status']='UNREADABLE'; rows.append(r); continue
        t1=re.sub(r'\s+',' ',d[0].get_text())
        r['pages']=len(d); r['textlen']=len(t1)
        r['code_ok']=f'9701/{v}' in t1
        r['paper2']=bool(re.search(r'Paper 2',t1))
        r['title']=('AS Level Structured Questions' in t1, 'AS Structured Questions' in t1, 'Structured Question' in t1)
        r['series_ok']=any(f'{n} 20{y:02d}' in t1 for n in SER[s])
        r['series_txt']=[n for n in ('February/March','March','May/June','October/November') if n in t1]
        r['is_ms']=bool(re.search(r'MARK SCHEME|Mark Scheme',t1))
        r['type_ok']=(r['is_ms']==(t=='ms'))
        r['paper3']='Paper 3' in t1
        r['status']='OK' if (r['code_ok'] and r['paper2'] and r['series_ok'] and r['type_ok'] and any(r['title'])) else 'HEADER_MISMATCH'
        rows.append(r)
json.dump(rows,open(sys.argv[1],'w'),indent=0)
from collections import Counter
print('expected files',len(rows),Counter(r['status'] for r in rows))
for r in rows:
    if r['status']!='OK': print(r['file'],r['status'],{k:r.get(k) for k in ('code_ok','paper2','title','series_ok','type_ok','paper3','textlen')})
extra=set('data/'+x for x in os.listdir('data') if x.endswith('.pdf'))-set(r['file'] for r in rows); print('unexpected extra files:',sorted(extra))
