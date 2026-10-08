"""Check 3b: classify every leaf missing from the book against the exclusions stated in report.md."""
import json, re, sys
sys.path.insert(0,'hub/audit/scripts'); from a31_coverage import report_exclusions, expand
from collections import Counter
SER={'M/J':'s','O/N':'w','MAR':'m'}
def pk(ref): m=re.match(r'(M/J|O/N|MAR) (\d\d)/P(\d\d)',ref); return f"{SER[m.group(1)]}{m.group(2)}_{m.group(3)}"
R,ex=report_exclusions(); qp=json.load(open('hub/audit/out/qp_parse.json'))
cov=json.load(open('hub/audit/out/coverage.json'))
stated={}
for sec,L in ex.items():
    for pref,q,suf,issue,line in L:
        k=pk(pref)
        if q is None:
            for qq,P in qp[k]['parts'].items():
                for x in P: stated[(k,x)]=(sec,issue)
        else:
            leaves=list(qp[k]['parts'].get(q,{}).keys())
            scope=suf if suf else ''
            if scope=='' and 'whole' not in line and sec=='Paper-level verification failures': pass
            e=expand(int(q),suf,leaves) if suf else leaves
            for x in (e or []): stated[(k,x)]=(sec,issue)
# s20_23 header exclusion is in 'Downloads' section
for qq,P in qp['s20_23']['parts'].items():
    for x in P: stated.setdefault(('s20_23',x),('Downloads and header checks','ms: paper title not on page 1'))
out=[]; c=Counter()
for r in cov:
    if r['status']=='covered' or r['status']=='DUPLICATE': 
        if (r['paper'],r['leaf']) in stated and r['status']=='covered': c['IN BOOK but listed as excluded']+=1; out.append({**r,'cls':'IN BOOK but listed as excluded','stated':stated[(r['paper'],r['leaf'])]})
        continue
    s=stated.get((r['paper'],r['leaf']))
    if r['status']=='MISSING':
        cls='missing, reason stated in report.md' if s else 'MISSING, NO STATED REASON'
    else:
        cls='excluded by me too; build reason stated' if s else 'excluded by me; build has no stated reason'
    c[cls]+=1; out.append({**r,'cls':cls,'stated':s})
json.dump(out,open('hub/audit/out/missing_classified.json','w'),indent=0)
print(dict(c))
for o in out:
    if o['cls'] in ('MISSING, NO STATED REASON','IN BOOK but listed as excluded','excluded by me; build has no stated reason'): print(o['cls'][:12],o['paper'],o['leaf'],o.get('stated'),o['items'][:1])
