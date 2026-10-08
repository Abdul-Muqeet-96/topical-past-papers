"""Check 5a: per-part QP marks vs MS marks (my parsers). Compare at the finest common level:
leaf if the MS labels the leaf, else roll up to the lettered part."""
import json, re
qp=json.load(open('hub/audit/out/qp_parse.json')); ms=json.load(open('hub/audit/out/ms_parse.json'))
res=[]
for k in qp:
    for q,P in qp[k]['parts'].items():
        M=ms.get(k,{}).get('parts',{}).get(q,{})
        if sum(M.values())!=sum(P.values()): continue   # question already fails check 4
        letters=sorted(set(re.match(r'\d+(\([a-z]\))?',x).group(0) for x in P))
        for L in letters:
            qleaves={x:v for x,v in P.items() if x==L or x.startswith(L+'(')}
            mleaves={x:v for x,v in M.items() if x==L or x.startswith(L+'(')}
            if set(qleaves)==set(mleaves):
                for x in qleaves: res.append((k,x,qleaves[x],mleaves[x],'leaf'))
            else:
                res.append((k,L,sum(qleaves.values()),sum(mleaves.values()),'letter-rollup'))
json.dump(res,open('hub/audit/out/part_marks.json','w'))
bad=[r for r in res if r[2]!=r[3]]
print(len(res),'comparisons;',len(bad),'mismatch'); [print(b) for b in bad]
