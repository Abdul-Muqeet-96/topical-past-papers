"""Part B, independent of the pipeline: (1) my own QP reader (adapted from a20: left-margin question
numbers, (a)/(i) labels, [n] marks, [Total: n]; Data/Formulae and blank pages skipped) -> QP-side checks
per paper; (2) my own MS reader: per question, the sum of unbracketed B/C/M/A codes in the Marks column;
(3) coverage: every lowest-level part of every included paper appears in exactly one question-side
item heading of the book; (4) item marks in index.csv = sum of my QP marks of the parts it covers."""
import csv, json, os, re, sys
from collections import defaultdict, Counter
import pymupdf as f
from pc_common import lines, ROOT, WB, WORK, load, save, pkey
from a03_lines import vwords
ROM = 'i|ii|iii|iv|v|vi|vii|viii|ix|x'
def parse_qp(fn):
    d = f.open(fn); ev = []; qs = []; st = {'L': None, 'Lx': 0}
    for pno, p in enumerate(d):
        if pno == 0:
            continue
        txt = p.get_text()
        if 'BLANK PAGE' in txt and len(txt.strip()) < 400:
            continue
        if pno in (1, 2) and re.search(r'^\s*(Data|Formulae)\s*$', txt, re.M) and 'acceleration of free fall' in txt:
            continue
        for l in lines(p):
            W = [w for w in l['w'] if 30 <= w[0] <= 570]
            if not W:
                continue
            y = l['c']
            if y < 48 or y > 800:
                continue
            if any(('UCLES' in w[4]) or '©' in w[4] or re.fullmatch(r'9702/\d\d/.*', w[4]) or w[4] == 'Turn' for w in W):
                continue
            k = 0
            if re.fullmatch(r'\d{1,2}', W[0][4]) and 44 <= W[0][0] <= 57:
                qs.append(int(W[0][4])); ev.append(('Q', int(W[0][4]))); k = 1; st['L'] = None
            for w in W[k:k + 3]:
                m = re.fullmatch(r'\(([a-z]+)\)', w[4])
                if not m or w[0] > 115:
                    break
                t = m.group(1)
                isrom = re.fullmatch(ROM, t) and not (t == 'i' and st['L'] == 'h' and abs(w[0] - st['Lx']) < 6)
                if isrom and st['L'] is not None:
                    ev.append(('R', t))
                elif re.fullmatch('[a-z]', t):
                    ev.append(('L', t)); st['L'] = t; st['Lx'] = w[0]
                else:
                    break
            for i, w in enumerate(W):
                m = re.search(r'\[(\d{1,2})\]$', w[4])
                if m and w[2] > 470:
                    ev.append(('M', int(m.group(1))))
                if w[4] == '[Total:' and i + 1 < len(W):
                    m2 = re.fullmatch(r'(\d{1,2})\]', W[i + 1][4])
                    if m2:
                        ev.append(('T', int(m2.group(1))))
    parts = {}; q = L = R = None; totals = defaultdict(list)
    for e in ev:
        if e[0] == 'Q':
            q = e[1]; L = R = None; parts.setdefault(q, {})
        elif e[0] == 'L':
            L, R = e[1], None
        elif e[0] == 'R':
            R = e[1]
        elif e[0] == 'M' and q is not None:
            key = f"{q}" + (f"({L})" if L else '') + (f"({R})" if R else '')
            parts[q][key] = parts[q].get(key, 0) + e[1]
        elif e[0] == 'T' and q is not None:
            totals[q].append(e[1])
    return {'qnums': qs, 'parts': parts, 'totals': dict(totals)}
def parse_ms(fn):
    d = f.open(fn); tot = Counter(); q = None
    for p in d:
        ws = vwords(p)
        hq = [w for w in ws if w[4] == 'Question' and w[1] < p.rect.height * 0.25]
        if not hq:
            continue
        mk = [w for w in ws if w[4] in ('Marks', 'Mark') and abs(w[1] - hq[0][1]) < 3]
        if not mk:
            continue
        mx0, mx1 = mk[0][0] - 12, mk[0][2] + 12      # the Marks column only (Guidance text may cite codes)
        for l in lines(p):
            W = l['w']
            m = re.fullmatch(r'(\d{1,2})\([a-h]\)(?:\([ivx]+\))?', W[0][4]) if W[0][0] < 120 else None
            if m:
                q = int(m.group(1))
            for k, w in enumerate(W):
                if mx0 <= w[0] <= mx1 and re.fullmatch(r'[BCMA][1-9]', w[4]) and q is not None:
                    nxt = W[k + 1] if k + 1 < len(W) else None
                    if nxt and nxt[0] - w[2] < 8 and re.match(r'[a-z]', nxt[4]):
                        continue          # 'C1 marks are independent' (Guidance text), not a mark
                    tot[q] += int(w[4][1])
    return dict(tot)
man = json.load(open(f'{WORK}/manifest_physics.json'))
chk = json.load(open(f'{WORK}/checks_partb.json'))
res = {'papers': {}, 'fail': []}
qp_all = {}
for pid, c in sorted(chk.items()):
    e = man[pid]
    qp = parse_qp(os.path.join(ROOT, 'data', e['qp']['file'])); ms = parse_ms(os.path.join(ROOT, 'data', e['ms']['file']))
    qp_all[pid] = qp
    N = max(qp['qnums']) if qp['qnums'] else 0
    sums = {q: sum(v.values()) for q, v in qp['parts'].items()}
    r = {'seq_ok': qp['qnums'] == list(range(1, N + 1)),
         'totals_ok': all(qp['totals'].get(q) == [sums[q]] for q in sums),
         'grand': sum(sums.values()),
         'ms_mismatch': {q: (ms.get(q), sums[q]) for q in sums if ms.get(q) != sums[q]},
         'pipeline_excluded': c['paper_excluded']}
    res['papers'][pid] = r
    if not (r['seq_ok'] and r['totals_ok'] and r['grand'] == 60):
        res['fail'].append((pid, 'QP-side check', r))
    if r['ms_mismatch']:
        res['fail'].append((pid, 'MS codes != QP total', r['ms_mismatch']))
# coverage from the book (question side, official items)
bi = load('book_items.json')
cover = defaultdict(list)
def expand(q, suf, leaves):
    if not suf:
        return leaves
    out = []
    for l, rs in re.findall(r'([a-z])(?:\(([ivx,]+)\))?', suf[1:]):
        if rs:
            out += [x for x in leaves if any(x == f'{q}({l})({r})' for r in rs.split(','))]
        else:
            out += [x for x in leaves if x == f'{q}({l})' or x.startswith(f'{q}({l})(')]
    return out
idx = {(r['reference'], int(r['page'])): r for r in csv.DictReader(open(os.path.join(WB, 'index.csv')))}
markfail = []
for it in bi:
    if it['side'] != 'Q' or it['booklet']:
        continue
    k, q, suf = pkey(it['ref'])
    leaves = list(qp_all[k]['parts'].get(q, {}).keys())
    e = expand(q, suf, leaves)
    if not e:
        res['fail'].append((it['ref'], 'reference does not expand to parts', suf))
        continue
    for x in e:
        cover[(k, x)].append(it['ref'])
    mine = sum(qp_all[k]['parts'][q][x] for x in e)
    r = idx.get((it['ref'], it['page']))
    if r is None or int(r['marks']) != mine:
        markfail.append((it['ref'], r and r['marks'], mine))
exp = [(k, x) for k, v in qp_all.items() if not res['papers'][k]['pipeline_excluded'] for q in v['parts'] for x in v['parts'][q]]
st = Counter()
miss, dup = [], []
for k, x in exp:
    c = cover.get((k, x), [])
    st['covered' if len(c) == 1 else 'DUPLICATE' if c else 'MISSING'] += 1
    if not c:
        miss.append((k, x))
    elif len(c) > 1:
        dup.append((k, x, c))
res['coverage'] = dict(st); res['missing'] = miss; res['dupes'] = dup; res['marks_fail'] = markfail
save('partb.json', res)
print('papers', len(res['papers']), '| fails', len(res['fail']), res['fail'][:6])
print('coverage', dict(st), 'missing', miss[:10], 'dupes', dup[:5], '| item marks != my QP marks:', len(markfail), markfail[:5])
