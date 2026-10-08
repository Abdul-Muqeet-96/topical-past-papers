"""Audit helper: compare QP vs MS part marks for one paper/question."""
import json,sys
sys.path.insert(0,'hub/audit/scripts'); from a21_ms_parse import parse_ms
k,q=sys.argv[1],sys.argv[2]
qp=json.load(open('hub/audit/out/qp_parse.json'))[k]['parts'][q]
ms=json.load(open('hub/audit/out/ms_parse.json'))[k]['parts'].get(q,{})
print('QP',qp); print('MS',ms)
s,v=k.split('_'); r=parse_ms(f'hub/data/9701_{s}_ms_{v}.pdf')
for x in r['raw']:
    if str(x[0])==q or len(sys.argv)>3: print(x)
