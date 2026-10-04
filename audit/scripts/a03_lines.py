"""Audit helper: words in VISUAL (rotation-corrected) coordinates grouped into lines."""
import pymupdf as f
def vwords(p):
    m=p.rotation_matrix; out=[]
    for w in p.get_text('words'):
        r=f.Rect(w[:4])*m; out.append((r.x0,r.y0,r.x1,r.y1,w[4]))
    return out
def lines(p,tol=3.5,merge=False):
    ws=sorted(vwords(p),key=lambda w:((w[1]+w[3])/2,w[0])); L=[]
    for w in ws:
        c=(w[1]+w[3])/2
        if L and abs(L[-1]['c']-c)<tol: L[-1]['w'].append(w)
        else: L.append({'c':c,'w':[w]})
    for l in L: l['w'].sort(key=lambda w:w[0])
    if merge:
        for l in L:
            out=[]
            for w in l['w']:
                if out and w[0] < out[-1][2]-0.3:
                    a=out[-1][4]; b=w[4]; k=0
                    for j in range(min(len(a),len(b)),0,-1):
                        if a.endswith(b[:j]): k=j; break
                    out[-1]=(out[-1][0],min(out[-1][1],w[1]),max(out[-1][2],w[2]),max(out[-1][3],w[3]),a+b[k:])
                else: out.append(w)
            l['w']=out
    return L
if __name__=='__main__':
    import sys; d=f.open(sys.argv[1]); p=d[int(sys.argv[2])]
    for l in lines(p)[:int(sys.argv[3]) if len(sys.argv)>3 else 60]:
        print(round(l['c']),' | '.join(f'{round(w[0])}:{w[4][:16]}' for w in l['w'])[:170])
