"""Check 8 helper: each item's OWN part text (context removed) for blind re-tagging."""
import json, re, sys
IT=json.load(open('hub/audit/out/item_text.json'))
out=[]
for v in sorted([v for v in IT.values() if v['side']=='Q'],key=lambda v:v['ref']):
    ref=v['ref']; suf=ref.split('/Q')[1]
    labs=re.findall(r'\(([a-z]+)\)',suf)
    first=labs[-1] if len(labs)>=2 and re.search(r'\([a-z]\)\([ivx]+\)',suf) else labs[0]
    if re.search(r'\([a-z]\)-\(',suf): first=labs[0]
    t=v['text']; pos=[m.start() for m in re.finditer(r'(?m)^\s*(?:\d+\s+)?(?:\([a-z]\)\s*)?\(%s\)'%re.escape(first),t)]
    own=t[pos[-1]:] if pos else t
    own=re.sub(r'\s+',' ',own)
    out.append({'ref':ref,'marks':None,'own':own})
json.dump(out,open('hub/audit/out/owntext.json','w'))
if len(sys.argv)>2:
    a,b=int(sys.argv[1]),int(sys.argv[2])
    for i,o in enumerate(out[a:b],a): print(i,o['ref'],'|',o['own'][:int(sys.argv[3]) if len(sys.argv)>3 else 200])
