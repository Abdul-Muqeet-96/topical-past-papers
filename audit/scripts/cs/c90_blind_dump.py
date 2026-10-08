"""Check 8 TOPICS (input for the blind re-tag). Every item of both books is written out without
its unit, section or outcome, in a shuffled order (seed 9618): a short piece of the question stem
and the text of the item's own parts, read from the raw question paper with the audit's own part
boundaries. The reader assigns a unit (1-12) to every line; c91 compares."""
import csv, random, re, sys
import pymupdf as f
from c00_common import *

QP = jl("qp_parse.json")
cache = {}


def page(fn, i):
    if fn not in cache:
        cache[fn] = f.open(os.path.join(DATA, fn))
    return cache[fn][i]


def toks(fn, i):
    p = page(fn, i)
    out = []
    for l in lines(p):
        if not (44 < l["c"] < p.rect.height - 44):
            continue
        t = " ".join(w[4] for w in l["w"])
        if re.search(r"©|UCLES|Cambridge University Press|\[Turn over|^\s*\d{4}/\d\d/[A-Z]/[A-Z]/\d\d\s*$|BLANK PAGE", t):
            continue
        for w in l["w"]:
            if re.search(r"papacambridge", w[4], re.I) or re.fullmatch(r"[.…_]{3,}", w[4]):
                continue
            if (w[0] > 560 or w[2] < 34) and w[4] in ("DO", "NOT", "WRITE", "IN", "THIS", "MARGIN"):
                continue                      # the 'DO NOT WRITE IN THIS MARGIN' strip of the 2025-26 papers
            if sum(ord(ch) > 0x2ff for ch in w[4]) >= 1 and len(w[4]) > 8 or sum(0x7f < ord(ch) < 0x250 for ch in w[4]) >= 4:
                continue                      # barcode glyphs
            out.append((l["c"], re.sub(r"[.…]{4,}", " ", w[4])))
    return out


def between(fn, a, b, npages):
    out = []
    for pg in range(a[0], min(b[0], npages) + 1):
        for y, t in toks(fn, pg - 1):
            if (pg > a[0] or y > a[1]) and (pg < b[0] or y <= b[1]):
                out.append(t)
    return out


items = []
for book in (1, 2):
    for r in csv.DictReader(open(os.path.join(BOOKDIR[book], "index.csv"))):
        items.append((book, r["reference"], int(r["unit"])))
random.seed(9618)
random.shuffle(items)
key = {}
os.makedirs(os.path.join(OUT, "blind"), exist_ok=True)
rows = []
for n, (book, ref, unit) in enumerate(items, 1):
    pid_, q, suf = ref_key(ref)
    code, sy, v = pid_.split("_")
    fn = f"{code}_{sy}_qp_{v}.pdf"
    P = QP[pid_]
    leaves = list(P["parts"][str(q)])
    marks = {k: [tuple(x) for x in v_] for k, v_ in P["pos"].items()}
    for qq, x in P["inner"].items():
        for k_, val, pg, y, x1 in x:
            marks.setdefault(k_, []).append((pg, y))
            if qq == str(q) and k_ not in leaves:
                leaves.append(k_)
    own = expand(q, suf, leaves)
    qstart = tuple(P["qpos"][str(q)])
    last = {l: max(marks[l]) for l in leaves if marks.get(l)}
    order = sorted(last, key=lambda l: last[l])
    prev = (qstart[0], qstart[1] - 6)
    reg = {}
    for l in order:
        reg[l] = (prev, (last[l][0], last[l][1] + 4))
        prev = reg[l][1]
    first = order[0] if order else None
    stem = between(fn, (qstart[0], qstart[1] - 6), reg[first][1], P["pages"])[:22] if first and first not in own else []
    txt = []
    for l in own:
        if l in reg:
            w = between(fn, reg[l][0], reg[l][1], P["pages"])
            if len(w) > 95:
                w = w[:45] + ["⟨…⟩"] + w[-45:]
            txt += w
    line = f"{n}| " + (" ".join(stem) + " ▸ " if stem else "") + " ".join(txt)
    rows.append(re.sub(r"\s+", " ", line))
    key[n] = {"book": book, "ref": ref, "unit": unit}
jd(key, "blind/key.json")
B = 75
for i in range(0, len(rows), B):
    open(os.path.join(OUT, "blind", f"batch_{i // B + 1:02d}.txt"), "w").write("\n".join(rows[i:i + B]) + "\n")
print(len(rows), "items in", (len(rows) + B - 1) // B, "batches; mean words", sum(len(r.split()) for r in rows) // len(rows))
