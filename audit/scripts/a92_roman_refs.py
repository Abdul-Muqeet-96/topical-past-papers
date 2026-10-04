"""Check 7b: references to sibling roman sub-parts ('in (ii)', 'your answer to (i)', 'from (ii) and
(iii)') whose sub-part is not shown in the item (no line starting with that label)."""
import json, re
IT=json.load(open('audit/out/item_text.json')); out=[]
for k,v in IT.items():
    if v['side']!='Q': continue
    t=v['text']
    labels=set(re.findall(r'(?m)^\s*(?:\d+\s+)?(?:\([a-z]\)\s*)?\(([ivx]+)\)',t))
    for m in re.finditer(r'(?:in|from|to|of|answers? to|answers? from|answers? in)\s+\(([ivx]+)\)(?:\s+and\s+\(([ivx]+)\))?',t):
        for g in [m.group(1),m.group(2)]:
            if g and g not in labels:
                ctx=t[max(0,m.start()-60):m.end()+30].replace('\n',' ')
                fallback=bool(re.search(r'If you were unable',t))
                out.append({'ref':v['ref'],'page':v['page'],'missing':f'({g})','fallback_given':fallback,'snippet':ctx})
seen={}
for o in out: seen.setdefault((o['ref'],o['missing']),o)
rows=list(seen.values()); json.dump(rows,open('audit/out/roman_refs.json','w'),indent=0)
print(len(rows)); [print(r['ref'],r['page'],r['missing'],'fallback' if r['fallback_given'] else '','|',r['snippet']) for r in rows]
