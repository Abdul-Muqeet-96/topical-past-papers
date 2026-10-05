"""Every placed crop band (Form XObject wrapping a source page, BBox = clip) on every book page, mapped to
its item (heading above it) and to its source page by text overlap: official QP/MS of the item's paper,
or the booklet-ocr.pdf page for booklet items."""
import bisect, json, re
from collections import defaultdict
import pymupdf as f
from pc_common import BOOK, BOOKLET, ROOT, load, save, pkey
d = f.open(BOOK)
bi = load('book_items.json')
seq = sorted(bi, key=lambda i: (i['page'], i['y']))
keys = [(i['page'], i['y']) for i in seq]
bands = []
for pno in range(len(d)):
    p = d[pno]
    for xref, name, inv, bbox in p.get_xobjects():
        if inv:
            continue
        obj = d.xref_object(xref)
        if '/fullpage' not in obj:
            continue
        m = re.search(r'/BBox \[ ([\d.\-]+) ([\d.\-]+) ([\d.\-]+) ([\d.\-]+) \]', obj)
        clip = [float(x) for x in m.groups()]
        fp = int(re.search(r'/fullpage (\d+) 0 R', obj).group(1))
        H = p.rect.height
        tr = f.Rect(bbox[0], H - bbox[3], bbox[2], H - bbox[1])
        k = bisect.bisect_right(keys, (pno + 1, (tr.y0 + tr.y1) / 2)) - 1
        it = seq[k] if k >= 0 else None
        bands.append({'page': pno + 1, 'target': list(tr), 'clip': clip, 'fp': fp,
                      'ref': it['ref'] if it else None, 'side': it['side'] if it else None,
                      'booklet': it['booklet'] if it else None, 'n': it['n'] if it else None,
                      'unit': it['unit'] if it else None, 'text': p.get_text(clip=tr + (1, 1, -1, -1))})
print('bands', len(bands))
toks = lambda s: set(re.findall(r'[A-Za-z]{3,}|\d+', s))
srcw = {}
def words(fn):
    if fn not in srcw:
        D = f.open(fn)
        srcw[fn] = [toks(pg.get_text()) for pg in D]
    return srcw[fn]
fptext, fpinfo = defaultdict(str), {}
for b in bands:
    fptext[b['fp']] += ' ' + b['text']
    fpinfo.setdefault(b['fp'], (b['ref'], b['booklet'], b['page']))
fpsrc = {}
for fp, t in fptext.items():
    ref, bk, page = fpinfo[fp]
    T = toks(t)
    if ref is None or not T:
        fpsrc[fp] = None
        continue
    if bk:
        cands = [BOOKLET]
    else:
        k, q, suf = pkey(ref)
        s, v = k.split('_')
        cands = [f'{ROOT}/data/9702_{s}_qp_{v}.pdf', f'{ROOT}/data/9702_{s}_ms_{v}.pdf']
    best = (0, None)
    for fn in cands:
        for i, S in enumerate(words(fn)):
            ov = len(T & S) / max(1, len(T))
            if ov > best[0]:
                best = (ov, (fn, i))
    fpsrc[fp] = {'match': best[1], 'overlap': round(best[0], 3)}
save('bands.json', {'bands': bands, 'fpsrc': {str(k): v for k, v in fpsrc.items()}})
lo = [(fp, v) for fp, v in fpsrc.items() if v and v['overlap'] < 0.8]
print('source pages placed', len(fpsrc), '; low-overlap mappings', len(lo), lo[:5])
print('bands without item', sum(1 for b in bands if b['ref'] is None), '(appendix)')
