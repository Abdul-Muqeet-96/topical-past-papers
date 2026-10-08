"""Check 2 (MS side), independent parser. Finds the Question/Answer/Marks table on each page,
reads part labels (compact '2(b)(ii)' or separate q/letter/roman columns), and marks from the
Marks column (and a Total / part-total column where the old layouts have one)."""
import pymupdf as f, re, json, sys
sys.path.insert(0,'hub/audit/scripts'); from a03_lines import lines
ROM='i|ii|iii|iv|v|vi|vii|viii|ix|x'
CMP=re.compile(r'(\d{1,2})((?:\([a-z]\))?)((?:\((?:%s)\))?)(?:\((?:%s)\))?$'%(ROM,ROM))
def num(t):
    m=re.fullmatch(r'\[?(\d{1,2})\]?',t); return int(m.group(1)) if m else None
def parse_ms(fn):
    d=f.open(fn); rec=[]; qtot={}; linerec=[]
    q=L=R=None; hdr=None
    for pno,p in enumerate(d):
        if pno==0: continue
        Ls=lines(p,merge=True)
        W0=p.rect.width if p.rotation in (0,180) else p.rect.height
        sc=W0/842 if W0>700 else W0/595*0.707
        found=False
        for l in Ls:
            T=[w[4] for w in l['w']]
            if 'Question' in T and any(t in ('Answer','Answers','Mark','Marks','Scheme','Total') for t in T):
                xs={w[4]:w[0] for w in l['w']}
                mk=[w[0] for w in l['w'] if w[4] in ('Mark','Marks')]
                tot=[w[0] for w in l['w'] if w[4]=='Total']
                ans=[w[0] for w in l['w'] if w[4] in ('Answer','Answers','Scheme')]
                gd=[w[0] for w in l['w'] if w[4]=='Guidance']
                hdr={'qx':xs['Question'],'mk':mk[-1] if mk else None,'tot':tot[0] if tot else None,'gd':gd[0] if gd else None,'y':l['c']}
                found=True; break
        if not found: continue
        m=p.rotation_matrix
        vr=sorted(set(round((dd['rect']*m).x0) for dd in p.get_drawings() if (dd['rect']*m).height>40 and (dd['rect']*m).width<3))
        def col(x0,x1):
            lo=[v for v in vr if v<=x0+2]; hi=[v for v in vr if v>=x1-2]
            return (lo[-1],hi[0]) if lo and hi else None
        mkw=[w for w in [ww for l in Ls for ww in l['w'] if abs(l['c']-hdr['y'])<1] if w[4] in ('Mark','Marks')]
        tw=[w for w in [ww for l in Ls for ww in l['w'] if abs(l['c']-hdr['y'])<1] if w[4]=='Total']
        hdr['mkcol']=col(mkw[-1][0],mkw[-1][2]) if mkw else None
        hdr['totcol']=col(tw[0][0],tw[0][2]) if tw else None
        for l in Ls:
            if l['c']<=hdr['y']+2: continue
            ws=l['w']; T=[w[4] for w in ws]
            if any('UCLES' in t or t=='Page' and 'of' in T for t in T): continue
            # label zone: left of answer text
            lab_lim=hdr["qx"]+48*sc
            labw=[w for w in ws if w[0]<lab_lim]
            lt=''.join(w[4] for w in labw[:4]).replace(' ','')
            mm=re.match(r'^(\d{1,2})?\(?(\([a-z]\)|[a-z]\))?(\((?:%s)\))?(\((?:%s)\))?'%(ROM,ROM),lt)
            if lt and mm and mm.group(0):
                g1,g2,g3=mm.group(1),mm.group(2),mm.group(3)
                if g2 and not g2.startswith('('): g2='('+g2
                if g1: q=int(g1); L=R=None
                if g2:
                    t=g2[1:-1]
                    # a bare '(i)'/'(v)'/'(x)' after a letter is a roman sub-part (separate-column layouts)
                    if not g1 and not g3 and re.fullmatch(ROM,t) and L is not None and not (t=='i' and L=='h'): R=t
                    else: L=t; R=None
                if g3: R=g3[1:-1]
            linerec.append((q,L,R,pno,[w for w in ws]))
            if 'Total:' in T or (hdr['tot'] is None and any(w[4]=='Total' and w[0]>0.6*W0 for w in ws)):
                v=[num(w[4]) for w in ws if num(w[4]) is not None]
                if v and q: qtot.setdefault(q,[]).append(v[-1])
                continue
            for w in ws:
                v=num(w[4])
                if v is None or w[0]<lab_lim: continue
                if hdr['mkcol'] and not (hdr['totcol'] and hdr['totcol']!=hdr['mkcol']):
                    if hdr['mkcol'][0]<=w[0] and w[2]<=hdr['mkcol'][1]: col='M'
                    else: continue
                elif hdr['mkcol'] and hdr['totcol']:
                    if hdr['mkcol'][0]<=w[0] and w[2]<=hdr['mkcol'][1]: col='M'
                    elif hdr['totcol'][0]<=w[0] and w[2]<=hdr['totcol'][1]: col='T'
                    else: continue
                elif hdr['mk'] is not None and hdr['mk']-30*sc<=w[0]<=hdr['mk']+60*sc:
                    if hdr['tot'] is not None and w[0]>=hdr['tot']-15*sc: col='T'
                    else: col='M'
                elif hdr['tot'] is not None and hdr['tot']-15*sc<=w[0]<=hdr['tot']+60*sc: col='T'
                else: continue
                if hdr['gd'] is not None and w[0]>=hdr['gd']-5: continue
                rec.append((q,L,R,col,w[0],v,pno+1,round(l['c'])))
    # resolve per label
    parts={}
    for q,L,R,col,x,v,pg,y in rec:
        if q is None: continue
        key=f"{q}"+(f"({L})" if L else '')+(f"({R})" if R else '')
        parts.setdefault(q,{}).setdefault(key,{'M':[],'T':[],'xs':[]})
        parts[q][key][col].append(v); parts[q][key]['xs'].append(round(x))
    res={}
    for q,P in parts.items():
        # two right-hand number columns without a Total header (w16 style): right cluster = part totals
        xs=sorted(set(x for k in P for x in P[k]['xs']))
        out={}
        for k,c in P.items():
            if c['T']: out[k]=c['T']
            else:
                out[k]=c['M']
        res[q]=out
    return {'raw':rec,'parts':res,'qtot':qtot,'lines':linerec}
def collapse(res):
    """marks per label, handling Total-column layouts and two-cluster layouts."""
    out={}
    for q,P in res['parts'].items():
        q=int(q); recs=[r for r in res['raw'] if r[0]==q]
        xs=[r[4] for r in recs if r[3]=='M']
        hasT=any(r[3]=='T' for r in recs)
        right=None
        if not hasT and xs and max(xs)-min(xs)>25: right=max(xs)-12
        lab={}
        for r in recs:
            key=f"{r[0]}"+(f"({r[1]})" if r[1] else '')+(f"({r[2]})" if r[2] else '')
            lab.setdefault(key,{'M':0,'T':[]})
            if r[3]=='T' or (right is not None and r[4]>=right): lab[key]['T'].append(r[5])
            else: lab[key]['M']+=r[5]
        # drop a printed question total in the Total column (last T value == sum of the other T values)
        Tall=[(k,v) for k in lab for v in lab[k]['T']]
        if len(Tall)>=2 and Tall[-1][1]==sum(v for _,v in Tall[:-1]):
            lab[Tall[-1][0]]['T'].pop()
        o={}
        for k,c in lab.items():
            o[k]=sum(c['T']) if c['T'] else c['M']
        out[q]=o
    return out
if __name__=='__main__':
    src=json.load(open('hub/audit/out/sources.json')); out={}
    for r in src:
        if r['type']!='ms' or r['status']=='MISSING': continue
        key=f"{r['series']}{r['year']:02d}_{r['variant']}"
        res=parse_ms(r['file']); out[key]={'parts':collapse(res),'qtot':res['qtot']}
    json.dump(out,open('hub/audit/out/ms_parse.json','w'))
    qp=json.load(open('hub/audit/out/qp_parse.json'))
    nq=bad=0; rows=[]
    for k in sorted(qp):
        for q,P in qp[k]['parts'].items():
            nq+=1; qt=qp[k]['totals'][q][0]; ms=out.get(k,{}).get('parts',{}).get(int(q),{})
            mt=sum(ms.values())
            if mt!=qt: bad+=1; rows.append((k,q,qt,mt))
    json.dump(rows,open('hub/audit/out/ms_q_mismatch.json','w'))
    print(nq,'questions;',bad,'MS total != QP total')
    from collections import Counter; print(Counter(r[0][:1]+r[0][1:3] for r in rows))
    for r in rows[:60]: print(r)
