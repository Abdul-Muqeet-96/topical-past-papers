"""Check 3 COVERAGE. Expected lowest-level parts come from MY QP parse (a20) for every paper,
minus whole papers failing MY header check and questions failing MY MS-total check.
Book coverage comes from the item headings in the final PDF (question side only)."""
import json, re
from collections import defaultdict, Counter
ROM=['i','ii','iii','iv','v','vi','vii','viii','ix','x']
SER={'M/J':'s','O/N':'w','MAR':'m'}
def pkey(ref):
    m=re.match(r'(M/J|O/N|MAR) (\d\d)/P(\d\d)/Q(\d+)(.*)$',ref); return f"{SER[m.group(1)]}{m.group(2)}_{m.group(3)}",int(m.group(4)),m.group(5)
def expand(q,suf,leaves):
    """leaves: list of labels of question q, e.g. '3(b)(ii)'. Return the subset covered by suffix."""
    L=[x for x in leaves]
    if suf.startswith('/'):   # Physics-booklet style (fix branch): /a,b(i,ii)
        out=[]
        for l,rs in re.findall(r'([a-z])(?:\(([ivx,]+)\))?',suf[1:]):
            if rs: out+=[x for x in L if any(x==f'{q}({l})({r})' for r in rs.split(','))]
            else: out+=[x for x in L if x==f'{q}({l})' or x.startswith(f'{q}({l})(')]
        return out
    m=re.fullmatch(r'\(([a-z])\)-\(([a-z])\)',suf)
    if m: a,b=m.groups(); return [x for x in L if re.match(rf'{q}\(([a-z])\)',x) and a<=re.match(rf'{q}\(([a-z])\)',x).group(1)<=b]
    m=re.fullmatch(r'\(([a-z])\)\(([ivx]+)\)-\(([ivx]+)\)',suf)
    if m:
        l,a,b=m.groups(); i0,i1=ROM.index(a),ROM.index(b)
        return [x for x in L if any(x==f'{q}({l})({r})' for r in ROM[i0:i1+1])]
    m=re.fullmatch(r'\(([a-z])\)\(([ivx]+)\)',suf)
    if m: return [x for x in L if x==f'{q}{suf}']
    m=re.fullmatch(r'\(([a-z])\)',suf)
    if m: return [x for x in L if x==f'{q}{suf}' or x.startswith(f'{q}{suf}(')]
    if suf=='': return L
    return None
def report_exclusions():
    R=open('Δ-chemistry/reports/report.md').read(); ex={}
    sec=None
    for line in R.splitlines():
        if line.startswith('## '): sec=line[3:]
        m=re.match(r'\| ((?:M/J|O/N|MAR) \d\d/P\d\d)(?:/Q(\d+)(\S*))? \| ([^|]+)\| ([^|]+)\|',line)
        m2=re.match(r'\| ((?:M/J|O/N|MAR) \d\d/P\d\d) \| (Q(\d+)|whole paper) \| ([^|]+)\|',line)
        if m2 and sec=='Paper-level verification failures':
            ex.setdefault(sec,[]).append((m2.group(1),m2.group(3),'',m2.group(4).strip(),line)); continue
        if m and sec in ('Paper-level verification failures','Item exclusions','Out-of-syllabus (Phase 2; not clearly covered by the 2025–27 learning outcomes)'):
            ex.setdefault(sec,[]).append((m.group(1),m.group(2),m.group(3),m.group(4).strip(),line))
    return R,ex
if __name__=='__main__':
    qp=json.load(open('hub/audit/out/qp_parse.json')); src=json.load(open('hub/audit/out/sources.json'))
    msm=json.load(open('hub/audit/out/ms_q_mismatch.json'))
    bad_hdr={f"{r['series']}{r['year']:02d}_{r['variant']}" for r in src if r['status']!='OK'}
    bad_q={(k,int(q)) for k,q,_,_ in msm}
    book=json.load(open('hub/audit/out/book_parse.json'))
    # question-side items: pages before the answers banner of their unit
    pages=book['pages']; ut=[p['i'] for p in pages if 'unit_title' in p]; ab=[p['i'] for p in pages if p.get('answers_banner')]
    def side(pg):
        for u,(a,b) in enumerate(zip(ut,ab)):
            nxt=ut[u+1] if u+1<len(ut) else 10**9
            if a<=pg<b: return u+1,'Q'
            if b<=pg<nxt: return u+1,'A'
        return None,None
    items=[]
    for it in book['items']:
        u,s=side(it['page']); it['unit']=u; it['side']=s; items.append(it)
    json.dump(items,open('hub/audit/out/book_items.json','w'))
    cover=defaultdict(list); unexpandable=[]
    for it in items:
        if it['side']!='Q': continue
        k,q,suf=pkey(it['ref']); leaves=list(qp.get(k,{}).get('parts',{}).get(str(q),{}).keys())
        e=expand(q,suf,leaves)
        if not e: unexpandable.append(it['ref']); continue
        for x in e: cover[(k,x)].append((it['ref'],it['unit'],it['page']))
    expected=[]
    for k,v in qp.items():
        for q,P in v['parts'].items():
            for x in P: expected.append((k,int(q),x))
    st=Counter(); rows=[]
    for k,q,x in expected:
        c=cover.get((k,x),[])
        reason='paper excluded (my header check)' if k in bad_hdr else 'question excluded (my MS check)' if (k,q) in bad_q else ''
        status='covered' if len(c)==1 else 'DUPLICATE' if len(c)>1 else ('excluded:'+reason if reason else 'MISSING')
        st[status]+=1; rows.append({'paper':k,'leaf':x,'status':status,'items':c})
    json.dump(rows,open('hub/audit/out/coverage.json','w'))
    print('expected leaves',len(expected),dict(st)); print('unexpandable refs',len(unexpandable),unexpandable[:10])
    extra=[k for k in cover if not any(r['paper']==k[0] and r['leaf']==k[1] for r in rows)]
    print('book leaves not in my QP parse',len(extra),extra[:10])
