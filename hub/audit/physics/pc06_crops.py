"""Crop checks on every placed band (adapted from hub/audit/scripts a71-a82, a74, a75, a80b):
 clipped  - source words only partly inside the union of an item's clips (10-90 %)
 cutfig   - official vector paths crossing a clip's top/bottom edge by >= 4 pt
 furniture- official: clip reaches the page-number/barcode or footer zone; booklet: clip reaches the
            running header / branding zone of the scan
 dots     - official dot-run words that are still visible (ink under them) in the book
 marks    - '[n]' mark boxes cut by a clip edge
 edgeink  - ink on the first/last pixel row inside a placed band (a glyph or line continues past it)
 sidecut  - words vertically inside a band but entirely left/right of its clip
 pagesplit- official bands contiguous in the source but on different book pages with ink across the cut
 dropped  - official ink-only strips (<= 60 pt) left out between two bands of one item
 space    - near-blank pages and interior gaps > 180 pt
 booklet regions - each booklet band equals one region of its item (work/booklet_items.json)"""
import json, re
from collections import defaultdict, Counter
import numpy as np
import pymupdf as f
from pc_common import BOOK, BOOKLET, WORK, load, save
o = load('bands.json')
fps = o['fpsrc']
d = f.open(BOOK)
idxp = next(i + 1 for i in range(len(d)) if 'Topic index: where each item was filed' in d[i].get_text())
pages = json.load(open(f'{WORK}/booklet_pages.json'))['pages']
cache = {}
def page(fn, i):
    if fn not in cache:
        cache[fn] = f.open(fn)
    return cache[fn][i]
grp = defaultdict(list)
for b in o['bands']:
    m = fps.get(str(b['fp']))
    if b['page'] >= idxp or not m or not m['match']:
        continue
    b['src'] = m['match']
    grp[(b['ref'], b['side'], b['unit'], b['n'], m['match'][0], m['match'][1])].append(b)
R = defaultdict(list)
def clips_of(p, bs):
    H = p.rect.height
    return [f.Rect(c[0], H - c[3], c[2], H - c[1]) for c in [b['clip'] for b in bs]]
def vwords(p):
    RM = p.rotation_matrix
    return [(f.Rect(w[:4]) * RM, w[4]) for w in p.get_text('words')]
MARG = {'DO', 'NOT', 'WRITE', 'IN', 'THIS', 'MARGIN'}
for (ref, side, unit, n, fn, pi), bs in grp.items():
    p = page(fn, pi)
    H, Wd = p.rect.height, p.rect.width
    cl = clips_of(p, bs)
    booklet = fn == BOOKLET
    tag = {'ref': ref, 'side': side, 'unit': unit, 'n': n, 'src': fn.split('/')[-1], 'srcpage': pi + 1,
           'bookpages': sorted({b['page'] for b in bs}), 'booklet': booklet}
    ws = vwords(p)
    for r, t in ws:
        if not t.strip() or r.height <= 0:
            continue
        inside = sum(max(0, min(r.y1, c.y1) - max(r.y0, c.y0)) * (1 if (r.x0 < c.x1 and r.x1 > c.x0) else 0) for c in cl) / r.height
        hx = [c for c in cl if c.y0 <= r.y0 + 1 and c.y1 >= r.y1 - 1]
        xin = max([max(0, min(r.x1, c.x1) - max(r.x0, c.x0)) / max(r.width, 0.1) for c in hx], default=1)
        if (0.12 < inside < 0.88 or (hx and 0.12 < xin < 0.88)) and not re.fullmatch(r'[.…]+', t):
            R['clipped'].append(dict(tag, word=t, vfrac=round(inside, 2), hfrac=round(xin, 2)))
        if re.fullmatch(r'[\[(|]\d{1,2}[\])|]|\[\d{1,2}\]|\[Total:|\d{1,2}\]', t) and 0.03 < inside < 0.97:
            R['marks'].append(dict(tag, word=t, inside=round(inside, 2)))
        cy = (r.y0 + r.y1) / 2
        for c in cl:
            if c.y0 < cy < c.y1 and (r.x1 <= c.x0 + 0.5 or r.x0 >= c.x1 - 0.5):
                if t in MARG or re.fullmatch(r'[*\d]+', t) or r.x1 < 12 or r.x0 > Wd - 12:
                    continue
                if booklet and (len(t) <= 2 or not re.search(r'[A-Za-z0-9]', t)):
                    continue      # OCR specks of scan noise at the page edge
                R['sidecut'].append(dict(tag, word=t, x=round(r.x0), clip_x=[round(c.x0), round(c.x1)]))
    if booklet:
        hb = pages[pi]['header_bottom'] or 0
        for c in cl:
            if c.y0 < hb - 1:
                R['furniture'].append(dict(tag, what=f'clip top {c.y0:.0f} above header bottom {hb:.0f}'))
        continue
    # official only
    top = bot = None
    for r, t in ws:
        if r.y1 < H * 0.075 and re.fullmatch(r'\d{1,2}', t) and abs((r.x0 + r.x1) / 2 - Wd / 2) < 25:
            top = max(top or 0, r.y1)
        if r.y0 > H * 0.85 and ('UCLES' in t or '©' in t or re.match(r'9702/\d\d/', t) or t == 'Turn'):
            bot = min(bot or H, r.y0)
    for c in cl:
        if top is not None and c.y0 < top - 2:
            R['furniture'].append(dict(tag, what='top zone (page number / barcode)'))
        if bot is not None and c.y1 > bot + 2:
            R['furniture'].append(dict(tag, what='footer zone'))
    iv = []
    for c in sorted(cl, key=lambda r: r.y0):
        if iv and c.y0 <= iv[-1][1] + 1.5:
            iv[-1][1] = max(iv[-1][1], c.y1)
        else:
            iv.append([c.y0, c.y1])
    RM = p.rotation_matrix
    for dd in p.get_drawings():
        if dd.get('fill_opacity') not in (None, 1) or dd.get('stroke_opacity') not in (None, 1):
            continue
        r = dd['rect'] * RM
        if r.width > Wd * 0.9 and r.height > H * 0.5:
            continue
        if Wd < 700 and (r.x1 < 35 or r.x0 > 560):
            continue
        if r.height < 1 and r.width > 200:
            continue
        for a, b2 in iv:
            for edge in (a, b2):
                if r.y0 < edge - 4 and r.y1 > edge + 4 and r.y1 > a and r.y0 < b2:
                    R['cutfig'].append(dict(tag, edge=round(edge, 1), path=[round(x) for x in r]))
# booklet bands must be exactly the regions of their item (book number -> booklet item via build_info)
info = json.load(open(f'{WORK}/build_info.json'))
BI = {f"B{i['unit']}-{i['n']}": i for i in json.load(open(f'{WORK}/booklet_items.json'))}
num2key = {}
for k, v in info['numbers'].items():
    if k.startswith('B') and k in BI:       # booklet items restored from official papers are not in BI
        num2key[(BI[k]['topic'], v)] = k
for (ref, side, unit, n, fn, pi), bs in grp.items():
    if fn != BOOKLET:
        continue
    if (unit, n) not in num2key:
        continue
    it = BI[num2key[(unit, n)]]
    regs = it['regions'] if side == 'Q' else it['answer_regions']
    p = page(fn, pi)
    for c in clips_of(p, bs):
        if not any(r[0] == pi and abs(r[1] - c.y0) < 1 and abs(r[2] - c.y1) < 1 for r in regs):
            R['booklet_region_mismatch'].append({'ref': ref, 'side': side, 'unit': unit, 'n': n, 'srcpage': pi + 1,
                                                 'clip_y': [round(c.y0, 1), round(c.y1, 1)]})
# rendered book: edge ink, visible dots, space
byp = defaultdict(list)
for b in o['bands']:
    if b['page'] < idxp and b.get('src'):
        byp[b['page']].append(b)
Z = 144 / 72
for pg in range(1, idxp):
    P = d[pg - 1]
    pm = P.get_pixmap(dpi=144, colorspace=f.csGRAY)
    a = np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.stride)[:, :pm.width]
    for b in byp.get(pg, []):
        x0, y0, x1, y1 = b['target']
        for edge, yy in (('top', int(y0 * Z) + 1), ('bottom', int(y1 * Z) - 2)):
            if 0 <= yy < a.shape[0]:
                n = int((a[yy, int(x0 * Z):int(x1 * Z)] < 110).sum())
                if n >= 3:
                    R['edgeink'].append({'page': pg, 'ref': b['ref'], 'side': b['side'], 'unit': b['unit'],
                                         'n': b['n'], 'edge': edge, 'dark_px': n, 'booklet': b['src'][0] == BOOKLET})
        if b['src'][0] != BOOKLET:
            tr = f.Rect(b['target'])
            for w in P.get_text('words', clip=tr):
                # fill-in blanks narrower than 60 pt (book scale) are kept on purpose (DOT_KEEP_W)
                if re.fullmatch(r'[.…]{6,}.*|.*[.…]{8,}', w[4]) and w[2] - w[0] >= 60 * tr.width / (b['clip'][2] - b['clip'][0]):
                    ww = a[int(w[1] * Z):int(w[3] * Z), int(w[0] * Z):int(w[2] * Z)]
                    if ww.size and (ww < 160).mean() > 0.02:
                        R['dots'].append({'page': pg, 'ref': b['ref'], 'side': b['side'], 'word': w[4][:20]})
    small = a[::5, ::5]
    body = small[int(48 * Z / 5):int(800 * Z / 5)]
    ink_rows = np.flatnonzero((body < 200).sum(axis=1) > 0)
    if len(ink_rows) < 3:
        R['space'].append({'page': pg, 'what': 'near-blank page'})
    else:
        gaps = np.diff(ink_rows) * 5 / Z
        big = [round(float(g)) for g in gaps if g > 180]
        if big:
            R['space'].append({'page': pg, 'what': f'interior gap(s) {big} pt'})
# official page splits and dropped ink (source rendered at 150 dpi)
Z2 = 150 / 72
rend = {}
for (ref, side, unit, n, fn, pi), bs in grp.items():
    if fn == BOOKLET:
        continue
    p = page(fn, pi)
    H = p.rect.height
    if (fn, pi) not in rend:
        pm = p.get_pixmap(dpi=150, colorspace=f.csGRAY)
        rend[(fn, pi)] = np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.stride)[:, :pm.width]
    a = rend[(fn, pi)]
    bs = sorted(bs, key=lambda b: H - b['clip'][3])
    for b1, b2 in zip(bs, bs[1:]):
        ya, yb = H - b1['clip'][1], H - b2['clip'][3]
        x0, x1 = int(42 * Z2), int(min(553, p.rect.width - 42) * Z2)
        if b1['page'] != b2['page'] and -1 < yb - ya <= 40:
            up = set(np.flatnonzero(a[int((ya - 1.5) * Z2), x0:x1] < 120))
            dn = set(np.flatnonzero(a[min(a.shape[0] - 1, int((yb + 1.5) * Z2)), x0:x1] < 120))
            if len(up & dn) >= 2:
                R['pagesplit'].append({'ref': ref, 'side': side, 'unit': unit, 'n': n, 'book_pages': [b1['page'], b2['page']],
                                       'cut_src_y': round(ya, 1), 'crossing_px': len(up & dn)})
        if side == 'Q' and 0.8 < yb - ya <= 60:
            strip = a[int(ya * Z2) + 1:int(yb * Z2) - 1, x0:x1] < 120
            ink = 0
            for row in strip:
                xs = np.flatnonzero(row)
                if not len(xs):
                    continue
                runs = np.split(xs, np.flatnonzero(np.diff(xs) > 1) + 1)
                short = [r for r in runs if len(r) <= 4]
                if len(short) >= 15 and len(short) >= 0.85 * len(runs):
                    continue        # dotted answer line
                ink += len(xs)
            words = [w for w in p.get_text('words') if ya + 0.5 < (w[1] + w[3]) / 2 < yb - 0.5 and 42 < w[0] < 553
                     and not set(w[4]) <= set('.…')]
            if ink >= 12 and not words:
                R['dropped'].append({'ref': ref, 'unit': unit, 'n': n, 'src': fn.split('/')[-1], 'srcpage': pi + 1,
                                     'dropped_y': [round(ya, 1), round(yb, 1)], 'ink_px': ink})
out = {k: v for k, v in R.items()}
save('crops.json', out)
print({k: len(v) for k, v in out.items()})
for k, v in out.items():
    items = sorted({(x.get('unit'), x.get('n'), x.get('side'), x.get('ref')) for x in v if 'ref' in x})
    print(k, len(v), 'in', len(items), 'items/answers', items[:12])
