"""Check 2 (QP side), independent parser. For each QP: question numbers (left-margin integers),
lettered parts, roman sub-parts, [n] marks and [Total: n], in reading order. Coordinates are
normalised to a 595-pt-wide page so A3-scaled files (e.g. s15) parse the same way."""
import pymupdf as f, re, json, sys
sys.path.insert(0,'hub/audit/scripts'); from a03_lines import lines
ROM='i|ii|iii|iv|v|vi|vii|viii|ix|x'
def parse_qp(fn):
    d=f.open(fn); ev=[]; tot={}; qs=[]; notes=[]; st={'L':None,'Lx':0}
    for pno,p in enumerate(d):
        if pno==0: continue
        s=p.rect.width/595.28 if p.rotation in (0,180) else p.rect.height/595.28
        txt=p.get_text()
        if 'BLANK PAGE' in txt and len(txt.strip())<60: continue
        if 'The Periodic Table of Elements' in txt: continue
        for l in lines(p):
            W=[(w[0]/s,w[1]/s,w[2]/s,w[3]/s,w[4]) for w in l['w'] if 30<=w[0]/s<=570]
            if not W: continue
            y=l['c']/s
            if y<48 or y>835: continue
            if any(('UCLES' in w[4]) or re.fullmatch(r'9701/\d\d/.*',w[4]) or w[4]=='Turn' for w in W): continue
            k=0
            if W and re.fullmatch(r'\d{1,2}',W[0][4]) and 44<=W[0][0]<=57:
                qs.append((int(W[0][4]),pno+1,round(y))); ev.append(('Q',int(W[0][4]),pno,y)); k=1; st['L']=None
            # letters / romans at line start
            for w in W[k:k+3]:
                m=re.fullmatch(r'\(([a-z]+)\)',w[4])
                if not m or w[0]>115: break
                t=m.group(1)
                isrom=re.fullmatch(ROM,t) and not (t=='i' and st['L']=='h' and abs(w[0]-st['Lx'])<6)
                if isrom and st['L'] is not None: ev.append(('R',t,pno,y))
                elif re.fullmatch('[a-z]',t): ev.append(('L',t,pno,y)); st['L']=t; st['Lx']=w[0]
                else: break
            for i,w in enumerate(W):
                m=re.search(r'\[(\d{1,2})\]$',w[4])
                if m and w[2]>470: ev.append(('M',int(m.group(1)),pno,y))
                if w[4]=='[Total:' and i+1<len(W):
                    m2=re.fullmatch(r'(\d{1,2})\]',W[i+1][4])
                    if m2: ev.append(('T',int(m2.group(1)),pno,y))
    parts={}; q=None; L=None; R=None; totals={}
    for e in ev:
        if e[0]=='Q': q=e[1]; L=R=None; parts.setdefault(q,{})
        elif e[0]=='L': L=e[1]; R=None
        elif e[0]=='R': R=e[1]
        elif e[0]=='M':
            key=f"{q}"+(f"({L})" if L else '')+(f"({R})" if R else '')
            if q is None: notes.append(f'mark before any question p{e[2]+1}'); continue
            parts[q][key]=parts[q].get(key,0)+e[1]
        elif e[0]=='T':
            if q is None: continue
            totals.setdefault(q,[]).append(e[1])
    return {'qnums':[x[0] for x in qs],'qpos':qs,'parts':parts,'totals':totals,'notes':notes,'pages':len(d)}
if __name__=='__main__':
    src=json.load(open('hub/audit/out/sources.json')); out={}
    for r in src:
        if r['type']!='qp' or r['status']=='MISSING': continue
        key=f"{r['series']}{r['year']:02d}_{r['variant']}"
        out[key]=parse_qp(r['file'])
    json.dump(out,open('hub/audit/out/qp_parse.json','w'))
    bad=0
    for k,v in out.items():
        qn=v['qnums']; N=max(qn) if qn else 0
        ok_seq=qn==list(range(1,N+1))
        sums={q:sum(v['parts'][q].values()) for q in v['parts']}
        tt={q:v['totals'].get(q) for q in v['parts']}
        ok_tot=all(tt[q] and len(tt[q])==1 and tt[q][0]==sums[q] for q in v['parts'])
        g=sum(t[0] for t in v['totals'].values() if t)
        if not(ok_seq and ok_tot and g==60):
            bad+=1; print(k,'seq',qn,'sums',sums,'totals',tt,'grand',g)
    print(len(out),'QPs parsed;',bad,'fail at least one QP-side check')
