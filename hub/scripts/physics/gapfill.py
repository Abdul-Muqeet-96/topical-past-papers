"""Fill the gaps the scanned booklet leaves (its printed pages 96-97, 144-145, 313-314, 328-329 and 534-535
are missing from the scan) with crops of the OFFICIAL Cambridge paper of the same question:
- items whose question is entirely on missing pages (only their answer survives in the scan),
- items whose question runs into missing pages (question replaced by the official question),
- answers that are missing or run into missing pages (answer replaced by the official mark scheme).
Nothing is retyped: the official QP/MS are cropped exactly as in Part B. Each paper is verified by its page-1
header, the question's part marks must add up to its [Total], and the MS marks must equal the QP total;
any failure leaves the gap as it was (reported). Writes work/gapfill.json. Prints counts only."""
import json, os, re, sys
import pymupdf
sys.path.insert(0, os.path.dirname(__file__))
from download import URL, fetch, verify
from parse import load, parse_qp, ms_rows, fix_ms_rows
from extract import build_question
from map_booklet import UNIT_TO_TOPIC

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
WORK = os.path.join(ROOT, "Ω-physics", "work")
DATA = os.path.join(ROOT, "hub", "data")
SER = {"M/J": "s", "O/N": "w", "MAR": "m"}
RE_REF = re.compile(r"^\s*(M\s*[/iI1l]?\s*J|[O0]\s*[/iI1l]?\s*N|MAR)\s*(\d\d)\s*/\s*P(\d\d)\s*/\s*Q(\d+)\s*$")


def norm_ref(s):
    m = RE_REF.match(s)
    if not m:
        return None
    g1 = m.group(1).replace(" ", "")
    ser = "MAR" if g1 == "MAR" else {"M": "M/J", "O": "O/N", "0": "O/N"}[g1[0]]
    return f"{ser} {m.group(2)}/P{m.group(3)}/Q{int(m.group(4))}"


def paper_files(ref):
    m = re.match(r"(M/J|O/N|MAR) (\d\d)/P(\d\d)/Q(\d+)", ref)
    s, yy, v, q = SER[m.group(1)], int(m.group(2)), int(m.group(3)), int(m.group(4))
    out = {}
    for kind in ("qp", "ms"):
        fn = f"9702_{s}{yy:02d}_{kind}_{v}.pdf"
        path = os.path.join(DATA, fn)
        if not os.path.exists(path):
            ok, why = fetch(URL.format(s=s, yy=f"{yy:02d}", kind=kind, v=v), path)
            if not ok:
                return None, f"{fn}: download failed ({why})"
        issues, notes, _ = verify(path, s, yy, v, kind)
        if issues:
            return None, f"{fn}: header check failed ({'; '.join(issues)})"
        out[kind] = fn
    return (out, q), ""


def text_ms(md, qn):
    """2015 physics mark schemes are free text, not a table: the question's block runs from its
    number in the left margin to the next question's number; its marks are the [n] it prints."""
    starts = []
    for p in range(1, md.page_count):
        for w in md[p].get_text("words"):
            if w[0] < 75 and re.fullmatch(r"\d{1,2}", w[4]) and w[1] > 60:
                starts.append((int(w[4]), p, w[1]))
    starts.sort(key=lambda s: (s[1], s[2]))
    me = [s for s in starts if s[0] == qn]
    if not me:
        return []
    _, p0, y0 = me[0]
    later = [s for s in starts if (s[1], s[2]) > (p0, y0)]
    p1, y1 = (later[0][1], later[0][2]) if later else (md.page_count - 1, 800)
    segs, marks = [], 0
    for p in range(p0, p1 + 1):
        foot = [w[1] for w in md[p].get_text("words") if w[1] > 780]
        top = y0 - 4 if p == p0 else 60
        bot = y1 - 4 if p == p1 else (min(foot) - 4 if foot else 800)
        if bot - top < 3:
            continue
        segs.append((p, pymupdf.Rect(40, top, 560, bot)))
        marks += sum(int(w[4][1:-1]) for w in md[p].get_text("words")
                     if re.fullmatch(r"\[\d+\]", w[4]) and top <= w[1] < bot)
    return [{"q": qn, "segs": segs, "mark_total": marks, "part": "", "label": str(qn), "marks": [marks]}]


def official(ref):
    """Question regions and MS row segments of a whole official question, after the checks."""
    pf, why = paper_files(ref)
    if pf is None:
        return None, why
    files, qn = pf
    qd = load(os.path.join(DATA, files["qp"]))
    md = load(os.path.join(DATA, files["ms"]))
    qs = parse_qp(qd)
    rows = ms_rows(md)
    fix_ms_rows(rows, qs)
    q = next((x for x in qs if x["n"] == qn), None)
    if q is None:
        return None, f"Q{qn} not found in {files['qp']}"
    ps = sum(m["value"] for m in q["marks"])
    rq = [r for r in rows if r["q"] == qn]
    if not rq:
        rq = text_ms(md, qn)
    msm = sum(r["mark_total"] for r in rq)
    if q["total"] is None:
        # 2015 papers print no [Total: n]: the part marks must equal the MS marks instead
        if ps != msm or ps == 0:
            return None, f"no [Total]; part marks {ps} != MS marks {msm}"
        q["total"] = ps
    elif ps != q["total"]:
        return None, f"part marks {ps} != [Total: {q['total']}]"
    if msm != q["total"]:
        return None, f"MS marks {msm} != QP total {q['total']}"
    i = qs.index(q)
    nxt = qs[i + 1]["start"] if i + 1 < len(qs) else (qd.page_count - 1, 800)
    Q = build_question(qd, q, nxt, rq)
    regions = list(Q["stem"]) + [r for L in Q["letters"] for r in L["full"]]
    segs = [[p, list(rc)] for r in rq for p, rc in r["segs"]]
    return {"qp": files["qp"], "ms": files["ms"], "q": qn, "marks": q["total"], "regions": regions,
            "ms_segs": segs}, ""


def main():
    I = json.load(open(os.path.join(WORK, "booklet_items.json")))
    BP = json.load(open(os.path.join(WORK, "booklet_pages.json")))
    out = {"replace_q": {}, "replace_a": {}, "lost": [], "failed": []}
    for it in I:
        key = f"B{it['unit']}-{it['n']}"
        for fl in it["flags"]:
            kind = "replace_q" if fl.startswith("scan_gap_q") else "replace_a" if (
                fl.startswith("scan_gap_a") or fl == "no_answer") else None
            if not kind:
                continue
            o, why = official(it["ref"])
            if o is None:
                out["failed"].append([key, it["ref"], kind, why])
                continue
            o["flag"] = fl
            out[kind][key] = o
    for a in BP["orphan_answers"]:
        ref = norm_ref(a["ocr"])
        if ref is None:
            out["failed"].append([f"B{a['unit']}-{a['n']}", a["ocr"], "lost", "reference not readable"])
            continue
        o, why = official(ref)
        if o is None:
            out["failed"].append([f"B{a['unit']}-{a['n']}", ref, "lost", why])
            continue
        o.update({"ref": ref, "unit": a["unit"], "n": a["n"], "topic": UNIT_TO_TOPIC[a["unit"]],
                  "year": 2000 + int(ref.split(" ")[1][:2]), "answer_pdf": a["pdf"]})
        out["lost"].append(o)
    json.dump(out, open(os.path.join(WORK, "gapfill.json"), "w"), indent=0)
    print("questions replaced", len(out["replace_q"]), "| answers replaced", len(out["replace_a"]),
          "| lost items restored", len(out["lost"]), "| failed", len(out["failed"]))
    for f in out["failed"]:
        print("  failed", f)


if __name__ == "__main__":
    main()
