"""Visual text lines of the OCR'd booklet pages (words grouped by vertical overlap)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from ocr_booklet import read_tsv, OCR

_CACHE = {}


def words(pno):
    """OCR words of 1-based booklet page pno (points, page orientation as displayed)."""
    if pno not in _CACHE:
        _CACHE[pno] = read_tsv(os.path.join(OCR, f"p{pno:03d}.tsv"))
    return _CACHE[pno]


def vlines(pno, ws=None):
    """Words grouped into visual lines: list of dicts {y0, y1, x0, x1, words, text}, sorted by y.
    Tesseract lines are merged when they share most of their height (labels such as
    '1.' are often separate blocks from the text beside them)."""
    ws = words(pno) if ws is None else ws
    tl = {}
    for w in ws:
        tl.setdefault((w["block"], w["par"], w["line"]), []).append(w)
    lines = []
    for v in tl.values():
        lines.append({"y0": min(w["y0"] for w in v), "y1": max(w["y1"] for w in v), "words": list(v)})
    lines.sort(key=lambda l: (l["y0"] + l["y1"]) / 2)
    out = []
    for l in lines:
        c = (l["y0"] + l["y1"]) / 2
        h = l["y1"] - l["y0"]
        for o in out[-3:]:
            oh = o["y1"] - o["y0"]
            ov = min(o["y1"], l["y1"]) - max(o["y0"], l["y0"])
            ox0, ox1 = min(w["x0"] for w in o["words"]), max(w["x1"] for w in o["words"])
            lx0, lx1 = min(w["x0"] for w in l["words"]), max(w["x1"] for w in l["words"])
            xov = min(ox1, lx1) - max(ox0, lx0)      # pieces of one line sit side by side
            if ov > 0.55 * min(h, oh) and abs(c - (o["y0"] + o["y1"]) / 2) < 0.5 * max(h, oh) and xov < 2:
                o["words"] += l["words"]
                o["y0"], o["y1"] = min(o["y0"], l["y0"]), max(o["y1"], l["y1"])
                break
        else:
            out.append(dict(l))
    for o in out:
        o["words"].sort(key=lambda w: w["x0"])
        o["x0"] = o["words"][0]["x0"]
        o["x1"] = max(w["x1"] for w in o["words"])
        o["text"] = " ".join(w["text"] for w in o["words"])
    out.sort(key=lambda l: l["y0"])
    return out


def region_text(regions, xl=16, xr=580):
    """OCR text of booklet regions [[page0, y0, y1], ...] in reading order (lines joined by newlines)."""
    out = []
    for p0, y0, y1 in regions:
        for l in vlines(p0 + 1):
            c = (l["y0"] + l["y1"]) / 2
            if y0 - 0.5 <= c <= y1 + 0.5:
                ws = [w["text"] for w in l["words"] if w["x0"] >= xl and w["x1"] <= xr]
                if ws:
                    out.append(" ".join(ws))
    return "\n".join(out)


RE_MARKS = None


def printed_marks(text):
    """[n] marks printed in OCR text, tolerant of OCR bracket confusions: '[2]', '(2]', '[2)', '|2]'."""
    import re
    return [int(m.group(1)) for m in re.finditer(r"(?<![\w/])[\[(|{]\s*(\d{1,2})\s*[\])|}](?![\w])", text)
            if 0 < int(m.group(1)) <= 12]
