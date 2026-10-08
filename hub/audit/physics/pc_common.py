"""Shared paths and the book parser for the Physics self-check (adapted from hub/audit/scripts)."""
import json, os, re, sys
import pymupdf as f
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "hub", "audit", "scripts"))
from a03_lines import lines          # noqa: E402  (visual lines of a page)
OUT = os.path.join(HERE, "out")
WB = os.path.join(ROOT, "Ω-physics", "booklets", "p2-topical-workbook")
BOOK = os.path.join(WB, "Physics-9702-P2-Topical-Workbook.pdf")
BOOKLET = os.path.join(ROOT, "Ω-physics", "reference", "booklet-ocr.pdf")
WORK = os.path.join(ROOT, "Ω-physics", "build", "work")
REF = re.compile(r'^(\d+)\.\s+((?:M/J|O/N|MAR)\s\d\d/P\d\d/Q\d+\S*)\s*$')
SER = {'M/J': 's', 'O/N': 'w', 'MAR': 'm'}


def pkey(ref):
    m = re.match(r'(M/J|O/N|MAR) (\d\d)/P(\d\d)/Q(\d+)(.*)$', ref)
    return f"{SER[m.group(1)]}{m.group(2)}_{m.group(3)}", int(m.group(4)), m.group(5)


def parse(path):
    """Pages (header, unit title, answers banner) and every item heading 'n. REF' with page, y and
    whether the next line is the grey booklet source tag."""
    d = f.open(path)
    out = {'pages': [], 'items': []}
    for i, p in enumerate(d):
        L = lines(p)
        txt = p.get_text()
        head = [l for l in L if l['c'] < 40]
        pg = {'i': i + 1, 'header': [' '.join(w[4] for w in l['w']) for l in head]}
        m = re.match(r'\s*Unit (\d+)\n', txt)
        if m and 'items:' in txt:
            pg['unit_title'] = int(m.group(1))
        if re.search(r'^Answers Section$', txt, re.M) and not txt.startswith('Contents'):
            pg['answers_banner'] = True
        out['pages'].append(pg)
        for k, l in enumerate(L):
            t = ' '.join(w[4] for w in l['w'])
            mm = REF.match(t)
            if mm:
                nxt = ' '.join(w[4] for w in L[k + 1]['w']) if k + 1 < len(L) else ''
                out['items'].append({'n': int(mm.group(1)), 'ref': mm.group(2), 'page': i + 1,
                                     'y': round(l['c'], 1), 'booklet': nxt.startswith('booklet')})
    ut = [p['i'] for p in out['pages'] if 'unit_title' in p]
    ab = [p['i'] for p in out['pages'] if p.get('answers_banner')]
    for it in out['items']:
        it['unit'] = it['side'] = None
        for u, (a, b) in enumerate(zip(ut, ab)):
            nxt = ut[u + 1] if u + 1 < len(ut) else 10 ** 9
            if a <= it['page'] < b:
                it['unit'], it['side'] = u + 1, 'Q'
            elif b <= it['page'] < nxt:
                it['unit'], it['side'] = u + 1, 'A'
    return out


def save(name, obj):
    json.dump(obj, open(os.path.join(OUT, name), 'w'), indent=0, ensure_ascii=False)


def load(name):
    return json.load(open(os.path.join(OUT, name)))
