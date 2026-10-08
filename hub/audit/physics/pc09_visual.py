"""Visual-check sheets: for each selected item, its question side (from its heading to the next heading,
across pages) next to its answer side, rendered from the book at 90 dpi.
usage: pc09_visual.py OUTDIR select            -> writes out/visual_selection.json (selection rule below)
       pc09_visual.py OUTDIR render [u:n ...]   -> OUTDIR/v_<u>_<n>.png (default: the selection)
Selection: 3 official items per unit (first, middle, last in the unit) and 5 booklet items per unit
(newest, oldest and three spread between, preferring items with notes), plus every item named by an
automated crop flag (out/crops.json, out/selfcontained.json)."""
import json, os, sys
import pymupdf as f
from PIL import Image, ImageDraw
from pc_common import BOOK, load, save
out, mode = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
bi = load('book_items.json')
d = f.open(BOOK)
seq = sorted(bi, key=lambda i: (i['page'], i['y']))
def side_span(it):
    k = seq.index(it)
    nxt = seq[k + 1] if k + 1 < len(seq) else None
    segs = []
    p = it['page']
    while True:
        y0 = it['y'] - 12 if p == it['page'] else 40
        if nxt and nxt['page'] == p:
            segs.append((p, y0, nxt['y'] - 9))
            break
        segs.append((p, y0, 805))
        if nxt is None or p + 1 > nxt['page'] or p - it['page'] > 6:
            break
        p += 1
        if nxt['page'] == p and nxt['y'] < 75:
            break
    return segs
def render(segs, dpi=90):
    ims = []
    for p, y0, y1 in segs:
        if y1 - y0 < 4:
            continue
        pm = d[p - 1].get_pixmap(dpi=dpi, clip=f.Rect(25, y0, 575, y1))
        im = Image.frombytes('RGB', (pm.width, pm.height), pm.samples)
        ImageDraw.Draw(im).text((2, 2), f'p{p}', fill='red')
        ims.append(im)
    W = max(i.width for i in ims)
    S = Image.new('RGB', (W, sum(i.height + 4 for i in ims)), (200, 200, 200))
    y = 0
    for i in ims:
        S.paste(i, (0, y)); y += i.height + 4
    return S
if mode == 'select':
    sel = set()
    units = sorted({i['unit'] for i in bi})
    for u in units:
        q = [i for i in seq if i['unit'] == u and i['side'] == 'Q']
        off = [i for i in q if not i['booklet']]
        bk = [i for i in q if i['booklet']]
        for k in sorted({0, len(off) // 2, len(off) - 1}):
            sel.add((u, off[k]['n']))
        for k in sorted({0, len(bk) // 4, len(bk) // 2, 3 * len(bk) // 4, len(bk) - 1}):
            sel.add((u, bk[k]['n']))
    flags = []
    C = load('crops.json')
    for kind, rows in C.items():
        if kind in ('space',):
            continue
        for r in rows:
            if r.get('unit') and r.get('n'):
                sel.add((r['unit'], r['n'])); flags.append((kind, r['unit'], r['n']))
    for r in load('selfcontained.json'):
        if r['issues']:
            sel.add((r['unit'], r['n'])); flags.append(('selfcontained', r['unit'], r['n']))
    save('visual_selection.json', {'items': sorted(sel), 'flags': flags})
    print('selected', len(sel), 'items;', len(flags), 'flag rows')
else:
    keys = [tuple(int(x) for x in a.split(':')) for a in sys.argv[3:]] or [tuple(x) for x in load('visual_selection.json')['items']]
    for u, n in keys:
        q = next(i for i in seq if i['unit'] == u and i['n'] == n and i['side'] == 'Q')
        a = next(i for i in seq if i['unit'] == u and i['n'] == n and i['side'] == 'A')
        L, R = render(side_span(q)), render(side_span(a))
        S = Image.new('RGB', (L.width + R.width + 10, max(L.height, R.height) + 14), 'white')
        S.paste(L, (0, 14)); S.paste(R, (L.width + 10, 14))
        ImageDraw.Draw(S).text((2, 1), f"Unit {u} #{n} {q['ref']} {'booklet' if q['booklet'] else 'official'} | question left, answer right", fill='blue')
        S.save(os.path.join(out, f'v_{u:02d}_{n:02d}.png'))
    print('rendered', len(keys))
