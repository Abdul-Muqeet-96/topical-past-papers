"""Book structure: contents vs real pages, running headers and page numbers, no booklet branding, order
(Part B newest first, then booklet newest first), bookmarks, appendix (Data and Formulae)."""
import json, re
import pymupdf as f
from pc_common import BOOK, load, save
d = f.open(BOOK)
bp = load('book_parse.json')
bi = load('book_items.json')
info, F = {}, []
ct = d[1].get_text() + (d[2].get_text() if d[2].get_text().strip() and 'items:' not in d[2].get_text() else '')
ents = re.findall(r'^([^\n]+?)\s*\n?\.{3,}\s*\n?(\d+)\s*$', ct, re.M)
ents = [(a.strip(), int(b)) for a, b in ents]
units = [p['i'] for p in bp['pages'] if 'unit_title' in p]
ans = [p['i'] for p in bp['pages'] if p.get('answers_banner')]
idxp = next(i + 1 for i in range(len(d)) if 'Topic index: where each item was filed' in d[i].get_text())
appp = next(i + 1 for i in range(len(d)) if 'Appendix: Data and Formulae (from' in d[i].get_text())
exp = []
for k in range(len(units)):
    exp += [units[k], ans[k]]
exp += [idxp, appp]
got = [p for _, p in ents]
info['contents_entries'] = len(ents)
info['contents_match'] = got == exp
if got != exp:
    F.append(('contents pages', got, exp))
names = [n for n, _ in ents][0::2][:len(units)]
info['unit_names'] = names
bad_hdr, bad_num = [], []
for p in bp['pages']:
    i = p['i']
    h = ' '.join(p['header'])
    if i <= 2 or 'unit_title' in p:
        continue
    m = re.search(r'Workbook (\d+)', h)
    if not m or int(m.group(1)) != i:
        bad_num.append(i)
    u = max([k + 1 for k, s in enumerate(units) if s <= i] or [0])
    if 0 < u <= len(units) and i < idxp:
        isA = ans[u - 1] <= i
        want = f"Unit {u}: Answers Section" if isA else f"Unit {u}: {names[u - 1]}"
        if want not in h:
            bad_hdr.append((i, h[-50:], want))
info['pages_bad_header'] = len(bad_hdr)
info['bad_header_examples'] = bad_hdr[:5]
info['pages_bad_number'] = len(bad_num)
info['branding_hits'] = [i + 1 for i in range(len(d)) if re.search(r'Read\s*(&|and)\s*Write|Publications|Editorial Board|Article Number', d[i].get_text(), re.I)]
def key(ref):
    m = re.match(r'(M/J|O/N|MAR) (\d\d)/P(\d\d)', ref)
    return (int(m.group(2)), {'MAR': 0, 'M/J': 1, 'O/N': 2}[m.group(1)], -int(m.group(3)))
order_bad = []
for u in range(1, len(units) + 1):
    q = [i for i in sorted(bi, key=lambda i: (i['page'], i['y'])) if i['unit'] == u and i['side'] == 'Q']
    off = [i for i in q if not i['booklet']]
    bk = [i for i in q if i['booklet']]
    for a, b in zip(off, off[1:]):
        if key(a['ref'])[:2] < key(b['ref'])[:2]:
            order_bad.append((u, a['ref'], b['ref']))
    for a, b in zip(bk, bk[1:]):
        if key(a['ref'])[0] < key(b['ref'])[0]:
            order_bad.append((u, a['ref'], b['ref']))
info['newest_first_violations'] = len(order_bad)
info['order_examples'] = order_bad[:5]
toc = d.get_toc()
info['bookmarks'] = len(toc)
info['bookmarks_ok'] = len(toc) == 1 + 2 * len(units) + 2 and all(e[2] in (2, idxp, appp) or e[2] in units or e[2] in ans for e in toc)
last = d[-1].get_text()
info['appendix_has_data_and_formulae'] = all(s in last for s in ('Data', 'Formulae', 'acceleration of free fall', 'resistors in parallel'))
info['contents_fail'] = F
save('structure.json', info)
for k, v in info.items():
    print(k, ':', str(v)[:300])
