"""Part A steps 2-5: map the OCR'd Physics booklet.

Finds page roles (unit title pages, question pages, Answers Sections), the
running header of every page, every item heading "n. <reference>" in the
question and answer sections, and the page spans of each item and answer.
Headings whose reference fails the tolerant regex are listed in
Ω-physics/work/heading_reads.json and must be read by image (a cropped strip);
the values read are stored there and used on the next run.

Writes Ω-physics/work/booklet_pages.json and Ω-physics/work/booklet_items.json.
Prints counts only.
"""
import json, os, re, sys
from collections import defaultdict, Counter
import numpy as np
import pymupdf
sys.path.insert(0, os.path.dirname(__file__))
from booklet_lines import vlines, words

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "Ω-physics", "Physics paper 2 9702 3.pdf")
WORK = os.path.join(ROOT, "Ω-physics", "work")
READS = os.path.join(WORK, "heading_reads.json")

# Booklet contents page (pdf page 3), printed page numbers: unit -> (questions, answers).
# Read from the page image; the OCR of the page is checked against it below.
CONTENTS = {1: (5, 30), 2: (39, 59), 3: (65, 111), 4: (123, 167), 5: (179, 222), 6: (233, 270),
            7: (283, 327), 8: (338, 362), 9: (369, 410), 10: (421, 462), 11: (473, 517), 12: (531, 552)}
BOOKLET_UNITS = {1: "Physical Quantities And Units", 2: "Measurement Techniques", 3: "Kinematics",
                 4: "Dynamics", 5: "Forces, Density And Pressure", 6: "Work, Energy And Power",
                 7: "Deformation Of Solids", 8: "Waves", 9: "Superposition", 10: "Current Of Electricity",
                 11: "D.C Circuits", 12: "Particle And Nuclear Physics"}
# spec Part A step 4: booklet unit -> 2025-27 syllabus topic
UNIT_TO_TOPIC = {1: 1, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7, 9: 8, 10: 9, 11: 10, 12: 11}

HDR_KEYS = re.compile(r"Topical|Workbook|Publicat|Read and Write|Unit\s*\d|Answers?\s+Section|^\d{1,3}$", re.I)
SER = r"(?P<ser>M\s*[/iIl1|]?\s*/?\s*J|[O0]\s*[/iIl1|]?\s*/?\s*N|MAR|F\s*/?\s*M)"
D = r"[0-9OolISB]"
RE_REF = re.compile(SER + rf"\s*(?P<yy>{D}{{2}})\s*/\s*P\s*(?P<p>{D}{{2}})\s*/\s*[Q0O]\s*(?P<q>{D}{{1,2}})(?P<rest>.*)$")
RE_NUM = re.compile(r"^(\d{1,3})\s*[.,:;]$")
RE_NUMREF = re.compile(r"^(\d{1,3})\s*[.,:;]\s*(.+)$")
RE_PARTS = re.compile(r"^[a-h](?:\((?:i|ii|iii|iv|v|vi|vii)(?:,(?:i|ii|iii|iv|v|vi|vii))*\))?"
                      r"(?:,[a-h](?:\((?:i|ii|iii|iv|v|vi|vii)(?:,(?:i|ii|iii|iv|v|vi|vii))*\))?)*$")
SER_NORM = {"M": "M/J", "O": "O/N", "0": "O/N", "MAR": "MAR", "F": "F/M"}
XL, XR = 16, 580          # horizontal limits of scan content (scanner edge marks lie outside)
INK = 150                 # grey level below which a pixel counts as ink
Z = 1.5


def digits(s):
    return s.translate(str.maketrans("OolISB", "001158"))


def near(a, b):
    """Item numbers that differ in exactly one digit (OCR confusions such as 4/1, 9/1)."""
    sa, sb = str(a), str(b)
    if len(sa) == len(sb):
        return sum(x != y for x, y in zip(sa, sb)) == 1
    lo, hi = sorted((sa, sb), key=len)
    return len(hi) == len(lo) + 1 and any(hi[:k] + hi[k + 1:] == lo for k in range(len(hi)))


def align(hs, key, problems):
    """Item numbers along a section: keep the longest strictly increasing run of OCR
    numbers (they are almost always right); a candidate outside it is kept with a
    corrected number only when it sits in a gap of exactly one missing number that
    differs from its OCR number in one digit (e.g. '41.' between 10 and 12)."""
    n = len(hs)
    best, prev = [1 if hs[i]["n"] is not None else -10 ** 6 for i in range(n)], [-1] * n
    for i in range(n):
        if hs[i]["n"] is None:
            continue
        for j in range(i):
            if hs[j]["n"] is not None and hs[j]["n"] < hs[i]["n"] and best[j] + 1 > best[i]:
                best[i], prev[i] = best[j] + 1, j
    keep = set()
    i = max(range(n), key=lambda k: (best[k], -k)) if n else -1
    while i >= 0:
        keep.add(i)
        i = prev[i]
    out = []
    kl = sorted(keep)
    for i, h in enumerate(hs):
        if i in keep:
            out.append(h)
            continue
        lo_i = max([j for j in kl if j < i] or [-1])
        hi_i = min([j for j in kl if j > i] or [n])
        lo = hs[lo_i]["n"] if lo_i >= 0 else 0
        hi = hs[hi_i]["n"] if hi_i < n else 10 ** 3
        run = list(range(lo_i + 1, hi_i))          # outliers between the two kept neighbours
        slot = lo + 1 + run.index(i)
        if hi - lo - 1 == len(run) and all(hs[j]["n"] is None or hs[j]["n"] == lo + 1 + k or near(hs[j]["n"], lo + 1 + k)
                                           for k, j in enumerate(run)) and (h["parsed"] or h.get("added")):
            problems.append({"section": key, "issue": f"item number OCR '{h['n']}' read as {slot} "
                             f"(between {lo} and {hi})", "pdf": h["pdf"], "fixed": True,
                             "no_number": h["n"] is None})
            h["n_ocr"], h["n"] = h["n"], slot
            out.append(h)
        else:
            problems.append({"section": key, "issue": f"heading candidate n={h['n']} out of sequence "
                             f"(between {lo} and {hi})", "pdf": h["pdf"], "ocr": h["ocr"], "rejected": True})
    expect = 1
    for h in out:
        if h["n"] > expect:
            problems.append({"section": key, "issue": f"numbers {expect}..{h['n'] - 1} not found before "
                             f"pdf p{h['pdf']}", "pdf": h["pdf"], "missing": list(range(expect, h["n"]))})
        expect = h["n"] + 1
    return out


def parse_ref(text):
    """Tolerant parse of an item heading reference. Returns dict or None.
    'unambiguous' is True when the whole string was consumed by the grammar."""
    t = re.sub(r"[\s,;:|.'`]+$", "", text.strip())
    m = RE_REF.search(t)
    if not m:
        return None
    ser = m.group("ser").replace(" ", "")
    key = "MAR" if ser.upper() == "MAR" else ser[0].upper()
    yy, p, q = int(digits(m.group("yy"))), int(digits(m.group("p"))), int(digits(m.group("q")))
    rest = m.group("rest").strip().rstrip(".").strip()
    pre = t[:m.start()].strip()
    parts = None
    if rest:
        r = rest.replace(" ", "")
        r = re.sub(r"^[/,]", "", r)
        if r.startswith("(") and r.endswith(")") and re.fullmatch(r"\([a-h](,[a-h])*\)", r):
            r = r[1:-1]                                     # "(a,b)" -> "a,b"
        r = re.sub(r"^\(([a-h])\)", r"\1", r)               # "(a)(ii)" -> "a(ii)"
        r = r.replace(")(", ",")
        parts = r if RE_PARTS.match(r) else None
    unamb = parts is not None or not rest
    series = SER_NORM[key]
    ref = f"{series} {yy:02d}/P{p}/Q{q}" + (f"/{parts}" if parts else "")
    return {"series": series, "yy": yy, "paper": p, "q": q, "parts": parts, "rest": rest, "pre": pre,
            "ref": ref, "unambiguous": unamb and not pre}


def gray(page):
    pm = page.get_pixmap(matrix=pymupdf.Matrix(Z, Z), colorspace=pymupdf.csGRAY, alpha=False)
    return np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.stride)[:, :pm.width]


def ink_rows(a, x0=XL, x1=XR):
    """Boolean per pixel row: does the row carry ink (more than scan noise)?"""
    sub = a[:, int(x0 * Z):int(x1 * Z)] < INK
    return sub.sum(axis=1) >= 3


def trim(rows, y0, y1, a=None):
    """Shrink [y0, y1) to the first/last inked row; None if blank. With the page image a, a scan speck at
    either end (ink under 6 pt high and 30 pt wide, 40 pt or more away from the rest) is left out: it would
    stretch the crop over blank paper and faint show-through from the next sheet (physics fix)."""
    r0, r1 = max(0, int(y0 * Z)), min(len(rows), int(np.ceil(y1 * Z)))
    idx = np.flatnonzero(rows[r0:r1])
    if len(idx) == 0:
        return None
    if a is not None:
        runs = np.split(idx, np.flatnonzero(np.diff(idx) > 40 * Z) + 1)

        def speck(run):
            if (run[-1] - run[0] + 1) / Z >= 6:
                return False
            cols = np.flatnonzero((a[r0 + run[0]:r0 + run[-1] + 1, int(XL * Z):int(XR * Z)] < INK).any(axis=0))
            return len(cols) == 0 or (cols[-1] - cols[0] + 1) / Z < 30
        while len(runs) > 1 and speck(runs[-1]):
            runs.pop()
        while len(runs) > 1 and speck(runs[0]):
            runs.pop(0)
        idx = np.concatenate(runs)
    return (r0 + idx[0]) / Z - 1.5, (r0 + idx[-1] + 1) / Z + 1.5


def page_info(doc, pno):
    """Role, unit, printed number and header bottom for 1-based page pno."""
    L = vlines(pno)
    hdr = [l for l in L if l["y0"] < 112 and HDR_KEYS.search(l["text"])
           and not (re.fullmatch(r"\d{1,3}", l["text"]) and not (l["y0"] < 80 and 250 < l["x0"] < 340))]
    text_top = " | ".join(l["text"] for l in L if l["y0"] < 120)
    info = {"pdf": pno, "role": "other", "unit": None, "printed": None, "header_bottom": None,
            "header_text": " | ".join(l["text"] for l in hdr)}
    num = [w for l in L if l["y0"] < 90 for w in l["words"]
           if 250 < w["x0"] < 340 and re.fullmatch(r"\d{1,3}", w["text"])]
    if num:
        info["printed"] = int(num[0]["text"])
    alltext = " ".join(l["text"] for l in L)
    if re.search(r"Article Number|Editorial Board", alltext):
        info["role"] = "title"
        m = re.search(r"\bUnit\s*(\d{1,2})\b", alltext)
        info["unit"] = int(m.group(1)) if m else None
        return info
    m = re.search(r"Unit\s*(\d{1,2})\s*[:;]\s*(.*?)(?:\||$)", info["header_text"])
    if m:
        info["unit"] = int(m.group(1))
        info["role"] = "answers" if re.search(r"Answers?\s+Sec", m.group(2), re.I) else "questions"
    elif re.search(r"Answers?\s+Section", text_top, re.I):
        info["role"] = "answers"
    if hdr:
        # running header + branding (and the unit / Answers Section banner, when on this page)
        info["header_bottom"] = max(l["y1"] for l in hdr) + 3
    return info


def heading_candidates(pno, info):
    """Lines that look like item headings: '<n>. <reference>' in the leftmost column."""
    L = [l for l in vlines(pno) if info["header_bottom"] is None or l["y0"] > info["header_bottom"] - 1]
    if not L:
        return []
    out = []
    consumed = set()
    # left text column; lines starting with scan specks ('|', '.', '‘') do not count
    xs = sorted(l["x0"] for l in L if re.match(r"^[\w(\[]", l["words"][0]["text"]) and len(l["text"]) >= 4)
    left = xs[0] if xs else min(l["x0"] for l in L)
    for li, l in enumerate(L):
        w0 = l["words"][0]["text"]
        n, rest = None, ""
        # the heading's own words: stop at a wide gap (e.g. a mark '[1]' at the right margin)
        ws = [l["words"][0]]
        for w in l["words"][1:]:
            if w["x0"] - ws[-1]["x1"] > 30:
                break
            ws.append(w)
        while len(ws) > 2 and re.fullmatch(r"[,;:|.'`]+", ws[-1]["text"]):
            ws.pop()
        txt = " ".join(w["text"] for w in ws)
        # previous item's mark / dot leader printed on the heading line (a lone speck is not one)
        tail = [w for w in l["words"] if w["x0"] > ws[-1]["x1"] + 30 and re.search(r"\d|[.…]{3,}", w["text"])]
        hx1 = ws[-1]["x1"]
        hy1 = max(w["y1"] for w in ws)
        hwords = [[w["x0"], w["y0"], w["x1"], w["y1"]] for w in ws]
        m = RE_NUM.match(w0)
        if m and len(ws) == 1 and li + 1 < len(L) and L[li + 1]["y0"] - l["y1"] < 12 \
                and parse_ref(L[li + 1]["text"]) and L[li + 1]["x0"] < l["x1"] + 40:
            # number and reference read as two OCR lines (skewed scan): join them
            nl = L[li + 1]
            n, rest = int(m.group(1)), nl["text"]
            l = dict(l, y1=max(l["y1"], nl["y1"]), x1=max(l["x1"], nl["x1"]))
            consumed.add(li + 1)
            tail = [w for w in l["words"][1:] if w["x0"] > ws[0]["x1"] + 30] + \
                [w for w in nl["words"] if w["x0"] > nl["x0"] + 200]
            tail = [w for w in tail if re.search(r"\d|[.…]{3,}", w["text"])]
            hx1 = max(ws[0]["x1"], max([w["x1"] for w in nl["words"] if w["x0"] <= nl["x0"] + 200] or [0]))
            hy1 = max([ws[0]["y1"]] + [w["y1"] for w in nl["words"] if w["x0"] <= nl["x0"] + 200])
            hwords = [[w["x0"], w["y0"], w["x1"], w["y1"]] for w in [ws[0]] + [w for w in nl["words"]
                                                                              if w["x0"] <= nl["x0"] + 200]]
        elif m:
            n, rest = int(m.group(1)), " ".join(w["text"] for w in ws[1:])
        else:
            m = RE_NUMREF.match(txt)
            if m and re.match(r"^\d{1,2}[.,:;]", w0):
                n, rest = int(m.group(1)), m.group(2)
        if li in consumed:
            continue
        if n is None:
            # number not read by OCR (small digits): a line that starts with a reference in the
            # reference column; its number comes from the sequence (align)
            r0 = parse_ref(txt)
            if r0 and not r0["pre"] and l["x0"] <= left + 40 and re.match(r"^\S{1,4}\s*\d", txt):
                out.append({"pdf": pno, "n": None, "y0": l["y0"], "y1": l["y1"], "x0": l["x0"], "x1": l["x1"],
                            "ocr": txt, "parsed": r0, "no_number": True, "hx1": hx1, "hy1": hy1, "hwords": hwords,
                            "tail": [[w["x0"], w["y0"], w["x1"], w["y1"]] for w in tail]})
            continue
        if l["x0"] > left + 22:          # skewed scans drift by up to ~15 pt down a page
            continue
        ref = parse_ref(rest)
        looks = bool(re.search(r"(M\s*\S?\s*/?\s*J|O\s*\S?\s*/?\s*N|MAR)\s*\S{2}\s*/|/\s*P\s*\S{2}|/\s*Q\s*\d", rest))
        if ref or looks:
            out.append({"pdf": pno, "n": n, "y0": l["y0"], "y1": l["y1"], "x0": l["x0"], "x1": l["x1"],
                        "ocr": rest, "parsed": ref, "hx1": hx1, "hy1": hy1, "hwords": hwords,
                        "tail": [[w["x0"], w["y0"], w["x1"], w["y1"]] for w in tail]})
    return out


def heading_strip(h, first):
    """White-out for a booklet heading line that the crop must include (skewed scan): one strip over the
    whole heading (gaps between its words too, where underline and slash ink sits outside the OCR word
    boxes), 2 pt lower than the words, but never over a word of the question's first line."""
    hw = h.get("hwords", [])
    if not hw:
        return []
    x0, x1 = min(b[0] for b in hw) - 2, max(b[2] for b in hw) + 3
    y0, y1 = min(b[1] for b in hw) - 1.5, max(b[3] for b in hw) + 2.5
    for w in first:
        if w["x0"] < x1 and w["x1"] > x0 and w["y0"] < y1:
            y1 = min(y1, w["y0"] - 0.3)
    y1 = max(y1, max(b[3] for b in hw) + 0.5) if y1 > min(b[3] for b in hw) else y1
    out = [[h["pdf"] - 1, x0, y0, x1, y1, "h"]]
    # heading words with no first-line word below them (the item number in the left margin): cover their
    # glyphs' full depth, which on a skewed scan reaches below the strip (physics fix)
    for b in hw:
        if not any(w["x0"] < b[2] + 3 and w["x1"] > b[0] - 2 and w["y0"] < b[3] + 6 for w in first):
            out.append([h["pdf"] - 1, b[0] - 2, b[1] - 1.5, b[2] + 3, b[3] + 4, "h"])
    return out


RE_MARKW = re.compile(r"[\[(|{]\s*\d{1,2}\s*[\])|}]?|\d{1,2}\s*[\])|}]")


def _same(w, b):
    return abs(w["x0"] - b[0]) < 0.5 and abs(w["y0"] - b[1]) < 0.5


def line_marks(h):
    """Marks '[n]' at the right margin on a heading's line. A mark there can end the previous item or
    belong to the first part under the heading (physics fix: it was always given to the previous item)."""
    top, bot = h["y0"] - 4, max(h.get("hy1", h["y1"]), h["y1"]) + 4
    return [w for w in words(h["pdf"]) if w["x0"] > 400 and RE_MARKW.fullmatch(w["text"])
            and top < (w["y0"] + w["y1"]) / 2 < bot]


def mark_owner(h, m, header_bottom):
    """'prev' or 'this': the mark goes with the nearer text line, the one above the heading (end of the
    previous item) or the first line below it."""
    hb = max(h.get("hy1", h["y1"]), h["y1"])
    ws = [w for w in words(h["pdf"]) if w["x1"] < 400 and w["y1"] - w["y0"] < 16
          and w["y0"] > (header_bottom or 0) and not any(_same(w, b) for b in h.get("hwords", []))]
    mc = (m["y0"] + m["y1"]) / 2
    above = [(w["y0"] + w["y1"]) / 2 for w in ws if (w["y0"] + w["y1"]) / 2 < h["y0"] - 1]
    below = [(w["y0"] + w["y1"]) / 2 for w in ws if (w["y0"] + w["y1"]) / 2 > hb + 1]
    pc = max(above) if above else -1e9
    nc = min(below) if below else 1e9
    return "prev" if mc - pc < nc - mc else "this"


def split_marks(h, header_bottom, role):
    """(non-mark tail boxes, marks owned by the previous item, marks owned by this item); boxes as lists.
    On question pages a mark on a heading's line always ends the previous question (its answer space
    comes before the mark); on answer pages it can be the first answer line's mark."""
    tail = h.get("tail", [])
    if role != "answers":
        return tail, [], []
    ms = line_marks(h)
    nonmark = [t for t in tail if not any(_same(m, t) for m in ms)]
    prev, this = [], []
    for m in ms:
        (prev if mark_owner(h, m, header_bottom) == "prev" else this).append([m["x0"], m["y0"], m["x1"], m["y1"]])
    return nonmark, prev, this


def main():
    doc = pymupdf.open(SRC)
    reads = json.load(open(READS)) if os.path.exists(READS) else {}
    pages = [page_info(doc, p) for p in range(1, doc.page_count + 1)]
    # printed page numbers: fill gaps by continuity, detect missing printed pages
    for i, pg in enumerate(pages):
        if pg["printed"] is None and i > 0 and pages[i - 1]["printed"]:
            pg["printed_guess"] = pages[i - 1]["printed"] + 1
    missing = []
    last = None
    for pg in pages:
        n = pg["printed"]
        if n is None:
            continue
        if last and n - last[1] > pg["pdf"] - last[0]:
            missing.append([last[1] + 1, n - 1, last[0], pg["pdf"]])
        last = (pg["pdf"], n)
    # unit / role by contents page ranges (printed numbers), checked against the headers
    def printed(pg):
        return pg["printed"] or pg.get("printed_guess")
    for pg in pages:
        n = printed(pg)
        if n is None:
            continue
        u = max((k for k, (q, a) in CONTENTS.items() if q <= n), default=None)
        if u is None:
            continue
        q, a = CONTENTS[u]
        role = "title" if n == q else ("answers" if n >= a else "questions")
        pg["contents_unit"], pg["contents_role"] = u, role
    disagree = [pg["pdf"] for pg in pages if pg.get("contents_unit") and pg["unit"] and
                (pg["unit"], pg["role"]) != (pg["contents_unit"], pg["contents_role"])]
    for pg in pages:
        if pg.get("contents_unit"):
            pg["unit"], pg["role"] = pg["contents_unit"], pg["contents_role"]
        ws = words(pg["pdf"])
        if any(w["text"] == "BLANK" for w in ws) and any(w["text"] == "PAGE" for w in ws) and len(ws) < 25:
            pg["role"] = "blank"            # a blank page of the booklet is never part of an item
    # headings
    secs = defaultdict(list)          # (unit, role) -> pages
    for pg in pages:
        if pg["role"] in ("questions", "answers") and pg["unit"]:
            secs[(pg["unit"], pg["role"])].append(pg["pdf"])
    heads = defaultdict(list)
    for (u, role), pl in secs.items():
        for p in pl:
            heads[(u, role)] += heading_candidates(p, pages[p - 1])
    # sequence check per section: keep candidates that follow 1,2,3...
    to_read, problems = [], []
    seqs = {}
    for key, hs in sorted(heads.items()):
        hs.sort(key=lambda h: (h["pdf"], h["y0"]))
        # headings added by image reading (found missing from the OCR)
        for k, r in reads.items():
            if r.get("add") and tuple(r["section"]) == key and not any(f"{h['pdf']}:{round(h['y0'])}" == k for h in hs):
                hs.append({"pdf": r["pdf"], "n": r["n"], "y0": r["y0"], "y1": r["y1"], "x0": 0, "x1": 0,
                           "ocr": "", "parsed": None, "added": True})
        for k, r in reads.items():
            if r.get("drop") and tuple(r["section"]) == key:
                hs[:] = [h for h in hs if f"{h['pdf']}:{round(h['y0'])}" != k]
        hs.sort(key=lambda h: (h["pdf"], h["y0"]))
        seq = align(hs, key, problems)
        for h in seq:
            k = f"{h['pdf']}:{round(h['y0'])}"
            h["key"] = k
            if not (h["parsed"] and h["parsed"]["unambiguous"]):
                if k in reads:
                    h["read"] = reads[k]
                    h["parsed"] = parse_ref(reads[k]["text"]) or {"ref": reads[k]["text"], "unambiguous": False}
                    h["source"] = "image"
                else:
                    to_read.append({"key": k, "pdf": h["pdf"], "y0": h["y0"], "y1": h["y1"], "n": h["n"],
                                    "ocr": h["ocr"], "section": list(key)})
            else:
                h["source"] = "ocr"
        seqs[key] = seq
    # spans
    gcache = {}
    def rows(p):
        if p not in gcache:
            g = gray(doc[p - 1])
            gcache[p] = (ink_rows(g), g)
        return gcache[p][0]
    def span(key, i):
        seq = seqs[key]
        h = seq[i]
        pl = secs[key]
        end = (seq[i + 1]["pdf"], seq[i + 1]["y0"] - 2) if i + 1 < len(seq) else (pl[-1], 842)
        if i + 1 < len(seq) and seq[i + 1]["n"] != h["n"] + 1:
            # headings lost between this item and the next: if a scan gap lies between them,
            # the content after the gap belongs to the lost items, so stop at the gap
            for a, b, pa, pb in missing:
                if h["pdf"] <= pa and pb <= seq[i + 1]["pdf"]:
                    end = (pa, 842)
                    break
        wos = []
        box = lambda b, pad=1.0: [b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad]
        nh = seq[i + 1] if i + 1 < len(seq) else None
        nmk, npv, nth = split_marks(nh, pages[nh["pdf"] - 1]["header_bottom"], key[1]) if nh is not None else ([], [], [])
        if nh is not None and (nmk or npv) and end == (nh["pdf"], nh["y0"] - 2):
            # the next heading's line also carries the end of this item (its last mark / dots):
            # take that line and white out the next heading itself (and a mark of the next item there)
            ty1 = max(t[3] for t in nmk + npv) + 1.5
            end = (nh["pdf"], ty1)
            wos += [[nh["pdf"] - 1] + box(b) + ["h"] for b in nh.get("hwords", [])]
            wos += [[nh["pdf"] - 1] + box(b) + ["t"] for b in nth if b[1] < ty1]
        elif nh is not None and end == (nh["pdf"], nh["y0"] - 2):
            # last line of this item lower than the next heading's top (skewed scan): take its full
            # height and white out the next heading's words that come inside
            last = [w for w in words(nh["pdf"]) if (w["y0"] + w["y1"]) / 2 < nh["y0"] - 1 and w["y1"] > end[1]
                    and w["y1"] - w["y0"] < 16 and w["y1"] <= nh["y0"] + 5
                    and not any(abs(w["x0"] - b[0]) < 0.5 and abs(w["y0"] - b[1]) < 0.5 for b in nh.get("hwords", []))
                    and not any(_same(w, b) for b in nth)]
            if last:
                end = (nh["pdf"], max(w["y1"] for w in last) + 1.0)
                wos += [[nh["pdf"] - 1] + box(b) + ["h"] for b in nh.get("hwords", []) if b[1] - 1 < end[1]]
        # the crop starts at the first line under the booklet's own heading ("n. reference"); the heading
        # (and a previous item's mark on its line) is whited out: the book prints its own number and the
        # reference above the crop (one numbering per unit). Starting at the first line's own top keeps
        # skewed lines whole.
        hmk, hpv, hth = split_marks(h, pages[h["pdf"] - 1]["header_bottom"], key[1])
        base = max(h.get("hy1", h["y1"]), max([t[3] for t in hmk + hpv] or [0]))
        hstart = base + 1.0
        below = [w for w in words(h["pdf"]) if (w["y0"] + w["y1"]) / 2 > base + 1 and w["y0"] < base + 25
                 and not any(_same(w, b) for b in hth)]
        first = []
        if below:
            c0 = min((w["y0"] + w["y1"]) / 2 for w in below)
            first = [w for w in below if (w["y0"] + w["y1"]) / 2 < c0 + 7]
        top = min(w["y0"] for w in first) - 1.0 if first else hstart
        top = min([top] + [b[1] - 1.0 for b in hth])
        if top < hstart:
            # the first line (or a mark of this item printed on the heading's line) reaches above the
            # heading's bottom: start there, white out the heading and the previous item's tail
            hstart = top
            wos += heading_strip(h, first)
            wos += [[h["pdf"] - 1] + box(t) + ["t"] for t in hmk + hpv]
        regs = []
        for p in range(h["pdf"], end[0] + 1):
            if p not in pl:
                continue
            pg = pages[p - 1]
            y0 = hstart if p == h["pdf"] else (pg["header_bottom"] or 60) + 1
            y1 = end[1] if p == end[0] else 842
            t = trim(rows(p), y0, y1, gcache[p][1])
            if t and t[1] - t[0] > 3:
                regs.append([p - 1, round(max(t[0], y0), 1), round(min(t[1], y1), 1)])
        return regs, [w for w in wos if any(r[0] == w[0] for r in regs)]
    items = []
    missing_sets = [(a, b, pa, pb) for a, b, pa, pb in missing]
    for (u, role), seq in sorted(seqs.items()):
        if role != "questions":
            continue
        answers = {h["n"]: (j, h) for j, h in enumerate(seqs.get((u, "answers"), []))}
        for i, h in enumerate(seq):
            regs, wos = span((u, role), i)
            it = {"unit": u, "topic": UNIT_TO_TOPIC[u], "n": h["n"], "heading_ocr": h["ocr"],
                  "heading_source": h.get("source", "unread"), "heading_key": h["key"],
                  "ref": h["parsed"]["ref"] if h.get("parsed") else None,
                  "ref_parsed": h.get("parsed"), "regions": regs, "whiteouts": wos, "flags": []}
            if h.get("read"):
                it["heading_read"] = h["read"]["text"]
            # printed pages missing from the scan between this heading and the next one:
            # the item runs into them (content lost)
            nxt = seq[i + 1]["pdf"] if i + 1 < len(seq) else secs[(u, role)][-1] + 1
            for a, b, pa, pb in missing_sets:
                if h["pdf"] <= pa and pb <= nxt:
                    it["flags"].append(f"scan_gap_q:{a}-{b}")
            if h["n"] in answers:
                j, ah = answers[h["n"]]
                it["answer_regions"], it["answer_whiteouts"] = span((u, "answers"), j)
                it["answer_heading_ocr"] = ah["ocr"]
                it["answer_ref"] = ah["parsed"]["ref"] if ah.get("parsed") else None
                aseq = seqs[(u, "answers")]
                anext = aseq[j + 1]["pdf"] if j + 1 < len(aseq) else secs[(u, "answers")][-1] + 1
                for a, b, pa, pb in missing_sets:
                    if ah["pdf"] <= pa and pb <= anext:
                        it["flags"].append(f"scan_gap_a:{a}-{b}")
            else:
                it["answer_regions"], it["answer_whiteouts"] = [], []
                it["flags"].append("no_answer")
            items.append(it)
    orphan_answers = []
    for (u, role), seq in sorted(seqs.items()):
        if role == "answers":
            qn = {h["n"] for h in seqs.get((u, "questions"), [])}
            orphan_answers += [{"unit": u, "n": h["n"], "ocr": h["ocr"], "pdf": h["pdf"]} for h in seq
                               if h["n"] not in qn]
    json.dump({"pages": pages, "missing_printed": missing, "role_disagree": disagree,
               "sections": {f"{u}:{r}": pl for (u, r), pl in secs.items()}, "problems": problems,
               "orphan_answers": orphan_answers},
              open(os.path.join(WORK, "booklet_pages.json"), "w"), indent=0)
    json.dump(items, open(os.path.join(WORK, "booklet_items.json"), "w"), indent=0, ensure_ascii=False)
    json.dump(to_read, open(os.path.join(WORK, "heading_to_read.json"), "w"), indent=0)
    per = Counter(it["unit"] for it in items)
    print("missing printed pages:", [(a, b) for a, b, _, _ in missing])
    print("role/unit disagreements header vs contents:", disagree[:20])
    print("items per booklet unit:", dict(sorted(per.items())), "total", len(items))
    print("answers per unit:", {u: len(seqs.get((u, 'answers'), [])) for u in sorted(per)})
    print("headings: by OCR", sum(1 for s in seqs.values() for h in s if h.get("source") == "ocr"),
          "by image", sum(1 for s in seqs.values() for h in s if h.get("source") == "image"),
          "to read", len(to_read))
    print("sequence problems:", len(problems), "orphan answers:", len(orphan_answers),
          "items without answer:", sum(1 for it in items if "no_answer" in it["flags"]))


if __name__ == "__main__":
    main()
