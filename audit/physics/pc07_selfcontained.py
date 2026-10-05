"""Self-containment of Part B items (adapted from a91/a92), on the text the book shows for each item
(the book page text inside the item's bands): every 'Fig. n.n'/'Table n.n' mentioned has its caption in
the item; part references '(x)', 'your answer to (x)(y)' and sibling romans point to parts shown; the
question stem (my own reading of the QP) is present."""
import json, re
from collections import defaultdict
import pymupdf as f
from pc_common import BOOK, load, save
o = load('bands.json')
d = f.open(BOOK)
txt = defaultdict(list)
for b in o['bands']:
    if b['side'] == 'Q' and not b['booklet'] and b['ref']:
        txt[(b['ref'], b['unit'], b['n'])].append((b['page'], b['target'][1], b['text']))
res = []
for (ref, unit, n), parts in txt.items():
    t = '\n'.join(x[2] for x in sorted(parts))
    issues = []
    caps = set(re.findall(r'(?m)^\s*(?:Table|Fig\.|Figure)\s*(\d+\.\d+)', t))
    for m in set(re.findall(r'\b(Table|Fig\.|Figure)\s*(\d+\.\d+)', t)):
        if m[1] not in caps:
            issues.append(('dangling ' + m[0], m[1]))
    suf = re.search(r'/Q\d+(.*)$', ref).group(1)
    own = set(re.findall(r'([a-z])', suf.split('(')[0])) if suf else set()
    shown = set(re.findall(r'(?m)^\s*(?:\d+\s+)?\(([a-h])\)', t))
    for m in re.finditer(r'(?:in|to|from|of|part|answers? to|calculated in|shown in|given in|described in|from)\s+(?:\d)?\(([a-h])\)(\(([ivx]+)\))?', t):
        if m.group(1) not in shown and m.group(1) not in own:
            issues.append(('dangling part ref', m.group(0)))
    romans = set(re.findall(r'(?m)^\s*(?:\d+\s+)?(?:\([a-z]\)\s*)?\(([ivx]+)\)', t))
    for m in re.finditer(r'(?:in|from|to|of|answers? to)\s+\(([ivx]+)\)', t):
        if m.group(1) not in romans:
            issues.append(('dangling roman ref', m.group(0)))
    res.append({'ref': ref, 'unit': unit, 'n': n, 'issues': issues})
save('selfcontained.json', res)
bad = [r for r in res if r['issues']]
print('official items', len(res), 'with issues', len(bad))
for r in bad:
    print(' ', r['ref'], r['unit'], r['n'], r['issues'])
