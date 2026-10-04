"""Stage 4 (structure): for every included question, find the regions of the
stem, lettered parts and roman sub-parts; their text; Table/Fig. captions and
blocks; cross-references (parts, tables/figs, defined labels); and the matching
mark-scheme rows. Writes work/parts_<phase>.json. Prints counts only.

Regions are lists of [page, y0, y1] on the de-rotated question paper.
"""
import json, os, re, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from parse import load, parse_qp, ms_rows, fix_ms_rows, page_lines, special_page, data_cut, ROMANS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOP = 52
RE_DOTS = re.compile(r"^[.…·_ ]{6,}$")
RE_CAP = re.compile(r"^(Table|Fig\.|Figure)\s*(\d+\.\d+)(?:\s*\[\d+\])?$")
RE_TREF = re.compile(r"(Table|Fig\.|Figure)\s*(\d+\.\d+)")
RE_PREF = re.compile(r"\(([a-h])\)(?:\s*\((i|ii|iii|iv|v|vi|vii|viii|ix|x)\))?|(?<![a-z)])\((i|ii|iii|iv|v|vi|vii|viii|ix|x)\)")
RE_NREF = re.compile(r"\b(reaction|equation|step|stage|process|experiment|route|sample|test)\s+(\d+)\b", re.I)
LABEL_NOUNS = r"(?:compound|compounds|substance|element|elements|ion|ions|molecule|molecules|isomer|isomers|product|products|reagent|reagents|solution|solid|gas|liquid|salt|structure|structures|species|acid|alcohol|alkene|ester|mixture|polymer|monomer|reactant|intermediate|catalyst|metal|oxide|chloride|atom|atoms|peak|peaks|and|or|,)"
RE_LAB = re.compile(r"(?<![A-Za-z0-9(\[–\-+=/])([A-Z])(?![A-Za-z0-9a-z+\-–=(\[²³⁺⁻])")


def content_bottom(page):
    allw = page.get_text("words")
    foot = [w[1] for w in allw if w[1] > 740 and (w[4] == "©" or re.fullmatch(r"9702/\d\d/\S+", w[4]))]
    return (min(foot) - 0.5) if foot else 794


def span(doc, a, b):
    """Region from position a=(page,y) to b=(page,y) (exclusive), skipping special pages."""
    (p1, y1), (p2, y2) = a, b
    out = []
    for p in range(p1, p2 + 1):
        if special_page(doc[p]):
            continue
        top = y1 if p == p1 else TOP
        bot = y2 if p == p2 else content_bottom(doc[p])
        cut = data_cut(doc[p])
        if cut is not None:
            bot = min(bot, cut - 2)
        if bot - top > 2:
            out.append([p, round(top - 1.5, 1), round(bot - 1.5, 1)])
    return out


def region_lines(doc, region):
    out = []
    for p, y0, y1 in region:
        for ws in page_lines(doc[p], bottom=content_bottom(doc[p])):
            ly0 = min(w[1] for w in ws)
            if y0 - 0.5 <= ly0 < y1:
                out.append((p, ws))
    return out


def text_of(doc, region, strip_labels=True):
    parts = []
    for p, ws in region_lines(doc, region):
        words = [w[4] for w in ws]
        if all(RE_DOTS.match(w) for w in words):
            continue
        if strip_labels:
            while words and re.fullmatch(r"\d{1,2}|\([a-z]\)|\((?:i|ii|iii|iv|v|vi|vii|viii|ix|x)\)", words[0]) \
                    and ws[0][0] < 125:
                words = words[1:]
                ws = ws[1:]
        words = [w for w in words if not RE_DOTS.match(w)]
        parts.append(" ".join(words))
    return " ".join(parts)


def captions(doc, region):
    caps = {}
    for p, ws in region_lines(doc, region):
        t = " ".join(w[4] for w in ws)
        m = RE_CAP.match(t.strip())
        if m:
            caps[f"{_norm(m.group(1))} {m.group(2)}"] = (p, min(w[1] for w in ws), max(w[3] for w in ws))
    return caps


def drawing_boxes(page):
    W = page.rect.width
    boxes = []
    for d in page.get_drawings():
        r = d["rect"]
        if r.x1 <= 40 or r.x0 >= W - 40 or (r.width > W * 0.9 and r.height > 600):
            continue   # margin furniture: corner marks, side bars
        if r.y1 <= TOP + 2:
            continue   # top barcode / corner marks
        if d.get("fill") == (1.0, 1.0, 1.0) and not d.get("color"):
            continue
        boxes.append((r.x0, r.y0, r.x1, r.y1))
    for img in page.get_image_info():
        x0, y0, x1, y1 = img["bbox"]
        if y1 - y0 > 3 and x1 - x0 > 3 and y0 > TOP and x0 > 25:
            boxes.append((x0, y0, x1, y1))
    return boxes


def _prose(ws):
    """A text line of question prose (not a figure label): a sentence of several
    words, a part label, or a [mark]."""
    t = " ".join(w[4] for w in ws)
    if RE_CAP.match(t.strip()):
        return True
    alpha = [w for w in ws if re.search(r"[A-Za-z]{2,}", w[4])]
    lab = (re.fullmatch(r"\d{1,2}", ws[0][4]) and ws[0][0] < 64) or \
        (re.fullmatch(r"\([a-z]\)|\((?:i|ii|iii|iv|v|vi|vii|viii|ix|x)\)", ws[0][4]) and ws[0][0] < 125)
    return (len(alpha) >= 6 or lab
            or re.search(r"\[\d+\]$", t) or re.search(r"[a-z)]{2,}[.:?]$", t) and len(alpha) >= 1
            or RE_TREF.search(t) and len(alpha) >= 3)


def block_for_ink(doc, cap_key, cap):
    """Crop region for a Table (caption above) or Fig. (caption below), grown
    over the rendered ink (audit A-001/A-003): from the caption, take ink runs
    separated by at most GAP pt, stopping at a line of question prose."""
    from crops import ink_runs, page_top
    GAP = 26
    p, cy0, cy1 = cap
    page = doc[p]
    bot = content_bottom(page)
    top = page_top(page)
    lines = page_lines(page, bottom=bot)
    def prose_in(y0, y1):
        return any(_prose(ws) for ws in lines
                   if y0 - 1 <= (min(w[1] for w in ws) + max(w[3] for w in ws)) / 2 <= y1 + 1)
    if cap_key.startswith("Table"):
        runs = [r for r in ink_runs(page, cy1, bot, []) if r[0] >= cy1 - 0.5]
        y1 = cy1
        for k, r in enumerate(runs):
            if r[0] - y1 > GAP or (k and prose_in(r[0], r[1])):
                break
            y1 = r[1]
        if y1 <= cy1 + 2:
            return None
        return [[p, round(cy0 - 2, 1), round(min(y1 + 2, bot), 1)]]
    runs = [r for r in ink_runs(page, top, cy0, []) if r[1] <= cy0 + 0.5]
    y0 = cy0
    for k, r in enumerate(reversed(runs)):
        if y0 - r[1] > GAP or (k and prose_in(r[0], r[1])):
            break
        y0 = r[0]
    if y0 >= cy0 - 2:
        return None
    return [[p, round(max(y0 - 2, top), 1), round(cy1 + 2, 1)]]


def block_for_drawings(doc, cap_key, cap):
    """Crop region for a Table (caption above) or Fig. (caption below)."""
    p, cy0, cy1 = cap
    page = doc[p]
    boxes = [b for b in drawing_boxes(page) if b[3] - b[1] < 700]
    bot = content_bottom(page)
    if cap_key.startswith("Table"):
        cl = [b for b in boxes if cy1 - 2 <= b[1] <= cy1 + 30]
        if not cl:
            return None
        y1 = max(b[3] for b in cl)
        grew = True
        while grew:
            grew = False
            for b in boxes:
                if b[1] <= y1 + 3 and b[3] > y1 and b[1] >= cy1 - 2:
                    y1 = b[3]
                    grew = True
        return [[p, round(cy0 - 2, 1), round(min(y1 + 2, bot), 1)]]
    # figure: drawing cluster ending just above the caption
    cl = [b for b in boxes if cy0 - 45 <= b[3] <= cy0 + 2]
    if not cl:
        return None
    y0 = min(b[1] for b in cl)
    grew = True
    while grew:
        grew = False
        for b in boxes:
            if b[3] >= y0 - 3 and b[1] < y0 and b[3] <= cy0 + 2:
                y0 = b[1]
                grew = True
    # include labels (text lines) just above the cluster
    lines = [min(w[1] for w in ws) for ws in page_lines(page, bottom=bot)]
    for ly in sorted(lines, reverse=True):
        if y0 - 16 <= ly < y0:
            y0 = ly
    return [[p, round(max(y0 - 2, TOP), 1), round(cy1 + 2, 1)]]


def block_for(doc, cap_key, cap):
    """Tables: drawing-based extent (ink-based only when that finds nothing).
    Figures: union of the drawing-based and ink-based extents, so strokes that
    get_drawings misses are kept (audit A-001/A-003) and nothing shrinks."""
    old = block_for_drawings(doc, cap_key, cap)
    new = block_for_ink(doc, cap_key, cap)
    if cap_key.startswith("Table"):
        return old or new
    if not (old and new):
        return old or new
    return [[old[0][0], min(old[0][1], new[0][1]), max(old[0][2], new[0][2])]]


def _norm(w):
    return "Fig." if w.startswith("Fig") else w


ELEMENT_LIKE = set("ABCFHIKNOPS")
RE_DEFN = re.compile(r"\b(?:compounds?|substances?|elements?|ions?|molecules?|isomers?|products?|reagents?|"
                     r"solutions?|solids?|gas|gases|liquids?|salts?|species|acids?|alcohols?|alkenes?|esters?|"
                     r"mixtures?|polymers?|monomers?|reactants?|intermediates?|catalysts?|metals?|oxides?|"
                     r"hydrocarbons?|halogenoalkanes?|bottles?|samples?|structures?|ketones?|aldehydes?|"
                     r"atoms?|isotopes?|peaks?|anions?|cations?|curves?|areas?|points?|experiments?|"
                     r"organic compounds?|labelled|labeled)\s+((?:[A-Z](?:\s*,\s*|\s+and\s+|\s+or\s+|\s+to\s+))*[A-Z])\b")


def defined_labels(text):
    out = set()
    for m in RE_DEFN.finditer(text):
        out |= set(re.findall(r"[A-Z]", m.group(1)))
    return out


def refs_in(text):
    tabs = sorted({f"{_norm(m.group(1))} {m.group(2)}" for m in RE_TREF.finditer(text)})
    parts = []
    for m in RE_PREF.finditer(text):
        if m.group(1):
            parts.append(f"({m.group(1)})" + (f"({m.group(2)})" if m.group(2) else ""))
        else:
            parts.append(f"(*)({m.group(3)})")   # sibling roman, letter resolved later
    nrefs = sorted({f"{m.group(1).lower()} {m.group(2)}" for m in RE_NREF.finditer(text)})
    labs = set()
    for m in RE_LAB.finditer(text):
        L = m.group(1)
        before = text[:m.start()].rstrip()
        prev = before.split(" ")[-1] if before else ""
        if L in ("A", "I"):
            if not re.fullmatch(LABEL_NOUNS, prev, re.I):
                continue
        labs.add(L)
    # labels such as "D2" (a non-element letter + digit) used for compounds in tables (audit A-010)
    for m in re.finditer(r"(?<![A-Za-z0-9(\[])([ADEGJLMQRTXZ])([1-9])(?![A-Za-z0-9])", text):
        labs.add(m.group(1) + m.group(2))
    your = bool(re.search(r"\b(use|using)\s+your\s+(answers?|values?)\b", text, re.I))
    return {"tabs": tabs, "parts": sorted(set(parts)), "nrefs": nrefs, "labels": sorted(labs), "your": your}


def ms_key(label):
    return label


def build_question(doc, q, nxt_start, rows_q):
    parts = q["parts"]
    end = (q["total_pos"][0], q["total_pos"][1]) if q["total_pos"] else nxt_start
    # stem
    first = parts[0]["start"] if parts else end
    stem = span(doc, q["start"], first) if parts and first != q["start"] else []
    if parts and first[0] == q["start"][0] and abs(first[1] - q["start"][1]) < 3:
        stem = []
    letters = []
    seq = parts
    for i, pt in enumerate(seq):
        if pt["roman"] is None:
            # full region: to next letter or end
            nxt = next((s["start"] for s in seq[i + 1:] if s["roman"] is None), end)
            intro_end = seq[i + 1]["start"] if i + 1 < len(seq) else end
            letters.append({"letter": pt["letter"], "label": pt["label"],
                            "full": span(doc, pt["start"], nxt),
                            "intro": span(doc, pt["start"], intro_end) if intro_end != pt["start"] else [],
                            "romans": []})
            # same-line letter+roman: intro empty
            if i + 1 < len(seq) and seq[i + 1]["roman"] and seq[i + 1]["start"] == pt["start"]:
                letters[-1]["intro"] = []
        else:
            nxt = seq[i + 1]["start"] if i + 1 < len(seq) else end
            if not letters:   # romans directly under the question (no letters)
                letters.append({"letter": None, "label": "", "full": span(doc, pt["start"], end),
                                "intro": [], "romans": []})
            letters[-1]["romans"].append({"roman": pt["roman"], "label": pt["label"],
                                          "region": span(doc, pt["start"], nxt)})
    if not parts:
        letters.append({"letter": None, "label": "", "full": span(doc, q["start"], end), "intro": [],
                        "romans": []})
    # marks
    mk = defaultdict(int)
    for m in q["marks"]:
        mk[m["label"]] += m["value"]
    msm = defaultdict(int)
    msrows = defaultdict(list)
    for r in rows_q:
        msm[r["part"]] += r["mark_total"]
        msrows[r["part"]].append({"label": r["label"], "segs": [[p, list(rc)] for p, rc in r["segs"]],
                                  "marks": r["mark_total"]})
    for L in letters:
        lab = L["label"]
        L["intro_text"] = text_of(doc, L["intro"])
        L["full_text"] = text_of(doc, L["full"])
        L["marks"] = sum(v for k, v in mk.items() if k.startswith(lab)) if lab else sum(mk.values())
        L["own_marks"] = mk.get(lab, 0)
        L["ms_marks"] = sum(v for k, v in msm.items() if k.startswith(lab)) if lab else sum(msm.values())
        L["ms_rows"] = [r for k in sorted(msrows, key=lambda k: _order(k)) if (k.startswith(lab) if lab else True)
                        for r in msrows[k]]
        L["ms_letter_level"] = lab in msrows and any(k != lab and k.startswith(lab) for k in mk)
        L["refs"] = refs_in(L["intro_text"])
        for R in L["romans"]:
            R["text"] = text_of(doc, R["region"])
            R["marks"] = mk.get(R["label"], 0)
            R["ms_marks"] = msm.get(R["label"], 0)
            R["ms_rows"] = msrows.get(R["label"], [])
            R["refs"] = refs_in(R["text"])
            for i, pr in enumerate(R["refs"]["parts"]):
                if pr.startswith("(*)"):
                    R["refs"]["parts"][i] = (f"({L['letter']})" if L["letter"] else "") + pr[3:]
        L["full_refs"] = refs_in(L["full_text"])
        L["full_refs"]["parts"] = [(f"({L['letter']})" if L["letter"] else "") + p[3:] if p.startswith("(*)") else p
                                   for p in L["full_refs"]["parts"]]
    all_region = span(doc, q["start"], end)
    caps = captions(doc, all_region)
    blocks = {k: block_for(doc, k, v) for k, v in caps.items()}
    stem_text = text_of(doc, stem) if stem else ""
    # first-occurrence map for labels and numbered refs (definition sites)
    order = [("stem", stem_text)]
    for L in letters:
        order.append((L["label"] or "Q", L["intro_text"]))
        for R in L["romans"]:
            order.append((R["label"], R["text"]))
    defined = defined_labels(" ".join(t for _, t in order))
    first_def = {}
    for where, t in order:
        r = refs_in(t)
        for lab in r["labels"]:
            if lab in ELEMENT_LIKE and lab not in defined:
                continue
            first_def.setdefault("L:" + lab, where)
        for n in r["nrefs"]:
            first_def.setdefault("N:" + n, where)
    cap_site = {}
    for k, (p, y0, y1) in caps.items():
        site = "stem"
        for L in letters:
            if _in(L["full"], p, y0):
                site = L["label"]
                for R in L["romans"]:
                    if _in(R["region"], p, y0):
                        site = R["label"]
        cap_site[k] = site
    return {"n": q["n"], "total": q["total"], "labels_defined": sorted(defined), "stem": stem, "stem_text": stem_text,
            "stem_refs": refs_in(stem_text), "letters": letters, "captions": {k: list(v) for k, v in caps.items()},
            "cap_site": cap_site, "blocks": blocks, "first_def": first_def,
            "ms_unmatched": sorted(k for k in msrows if not any(k == L["label"] or k.startswith(L["label"]) for L in letters if L["label"]))}


def _in(region, p, y):
    return any(rp == p and y0 - 1 <= y < y1 for rp, y0, y1 in region)


def _order(k):
    m = re.match(r"\(([a-z])\)(?:\(([ivx]+)\))?", k)
    if not m:
        return (0, 0)
    return (ord(m.group(1)), ROMANS.index(m.group(2)) + 1 if m.group(2) else 0)


def main():
    phase = sys.argv[1]
    man = json.load(open(os.path.join(ROOT, "Ω-physics", "work", "manifest_physics.json")))
    checks = json.load(open(os.path.join(ROOT, "Ω-physics", "work", f"checks_{phase}.json")))
    out = {}
    nq = nl = nr = 0
    for pid, chk in sorted(checks.items()):
        if chk["paper_excluded"]:
            continue
        ent = man[pid]
        qd = load(os.path.join(ROOT, "data", ent["qp"]["file"]))
        md = load(os.path.join(ROOT, "data", ent["ms"]["file"]))
        qs = parse_qp(qd)
        rows = ms_rows(md)
        fix_ms_rows(rows, qs)
        paper = {"pid": pid, "ref": chk["ref"], "year": ent["year"], "series": ent["series"],
                 "variant": ent["variant"], "qp": ent["qp"]["file"], "ms": ent["ms"]["file"],
                 "questions": []}
        for i, q in enumerate(qs):
            if not chk["questions"][str(q["n"])]["ok"]:
                continue
            nxt = qs[i + 1]["start"] if i + 1 < len(qs) else (qd.page_count - 1, 800)
            Q = build_question(qd, q, nxt, [r for r in rows if r["q"] == q["n"]])
            paper["questions"].append(Q)
            nq += 1
            nl += len(Q["letters"])
            nr += sum(len(L["romans"]) for L in Q["letters"])
        out[pid] = paper
    json.dump(out, open(os.path.join(ROOT, "Ω-physics", "work", f"parts_{phase}.json"), "w"), indent=0)
    print(f"{phase}: papers {len(out)}, questions {nq}, lettered parts {nl}, roman sub-parts {nr}")


if __name__ == "__main__":
    main()
