"""Book (question side) vs index.csv vs items.jsonl vs unit PDFs: same items, units, pages, sources and
order; numbering 1..N per unit; answers in the same order with the same numbers and references."""
import csv, glob, json, os, re
from collections import Counter
from pc_common import parse, load, save, WB
bi = load('book_items.json')
Q = sorted([i for i in bi if i['side'] == 'Q'], key=lambda i: (i['page'], i['y']))
A = sorted([i for i in bi if i['side'] == 'A'], key=lambda i: (i['page'], i['y']))
idx = list(csv.DictReader(open(os.path.join(WB, 'index.csv'))))
jl = [json.loads(l) for l in open(os.path.join(WB, 'items.jsonl'))]
F = []
def fail(kind, detail):
    F.append({'kind': kind, 'detail': detail})
key_book = Counter((i['ref'], i['page'], i['unit'], 'booklet' if i['booklet'] else 'official') for i in Q)
key_idx = Counter((r['reference'], int(r['page']), int(r['unit']), r['source']) for r in idx)
key_jl = Counter((r['reference'], r['page'], r['unit'], r['source']) for r in jl)
for a, b, name in [(key_book, key_idx, 'index.csv'), (key_book, key_jl, 'items.jsonl')]:
    for k in a - b:
        fail(f'in book not {name}', k)
    for k in b - a:
        fail(f'in {name} not book', k)
for r in idx:
    if r['source'] == 'official' and not r['marks']:
        fail('official item without marks in index.csv', r['reference'])
for r in jl:
    if not r['text'].strip():
        fail('empty text in items.jsonl', r['reference'])
    if r['source'] == 'booklet' and 'OCR' not in r.get('text_note', '') and 'official paper' not in r.get('text_note', ''):
        fail('booklet text not labelled OCR', r['reference'])
units = sorted({i['unit'] for i in Q})
for u in units:
    q = [i for i in Q if i['unit'] == u]
    a = [i for i in A if i['unit'] == u]
    if [i['n'] for i in q] != list(range(1, len(q) + 1)):
        fail('numbering not 1..N', u)
    if [(i['n'], i['ref']) for i in q] != [(i['n'], i['ref']) for i in a]:
        fail('answers differ from questions (number/ref/order)', u)
    seen_booklet = False
    for i in q:
        if i['booklet']:
            seen_booklet = True
        elif seen_booklet:
            fail('official item after booklet items', (u, i['ref']))
for fn in sorted(glob.glob(os.path.join(WB, 'units', '*.pdf'))):
    u = int(re.search(r'Unit-(\d+)', fn).group(1))
    o = parse(fn)
    up = [(i['n'], i['ref']) for i in o['items']]
    bk = [(i['n'], i['ref']) for i in sorted(bi, key=lambda i: (i['page'], i['y'])) if i['unit'] == u]
    if up != bk:
        fail('unit PDF items differ from book', (u, len(up), len(bk)))
    for it in o['items']:
        hdr = ' '.join(o['pages'][it['page'] - 1]['header'])
        num = re.search(r'Workbook (\d+)', hdr)
        bpage = next((j['page'] for j in bi if j['unit'] == u and j['n'] == it['n'] and j['ref'] == it['ref']
                      and j['side'] == (it['side'] if it['side'] else j['side'])), None)
        if not num:
            fail('unit PDF page without book page number', (u, it['page']))
save('threeway_fail.json', F)
print('book Q', len(Q), 'A', len(A), 'index rows', len(idx), 'items.jsonl', len(jl), '| failures', Counter(x['kind'] for x in F))
for x in F[:15]:
    print(' ', x)
