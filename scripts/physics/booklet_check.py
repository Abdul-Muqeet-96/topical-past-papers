"""Part A step 6: light check of the booklet (report only).

  python3 scripts/physics/booklet_check.py select   -> Ω-physics/work/booklet_sample.json, prints papers
  python3 scripts/physics/booklet_check.py marks    -> compares printed [marks] with the official QPs
  python3 scripts/physics/booklet_check.py summary  -> Ω-physics/work/booklet_check.json (all checks)

Printed marks of a sampled item are read from its right margin: the margin strip of
every item region is OCR'd again at 300 dpi with a bracket/digit whitelist.
"""
import json, os, re, subprocess, sys, tempfile
from collections import defaultdict, Counter
import pymupdf
sys.path.insert(0, os.path.dirname(__file__))
from booklet_lines import region_text, printed_marks
from map_booklet import CONTENTS, UNIT_TO_TOPIC, SRC

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.join(ROOT, "Ω-physics", "work")
SER_FILE = {"M/J": "s", "O/N": "w", "MAR": "m"}


def pid_of(rp):
    return f"{SER_FILE[rp['series']]}{rp['yy']:02d}_{rp['paper']}"


def select():
    I = json.load(open(os.path.join(WORK, "booklet_items.json")))
    by_topic = defaultdict(list)
    for it in I:
        if any(f.startswith("scan_gap") for f in it["flags"]) or "no_answer" in it["flags"]:
            continue
        by_topic[it["topic"]].append(it)
    sample = []
    for t in sorted(by_topic):
        its = sorted(by_topic[t], key=lambda i: (-i["ref_parsed"]["yy"], i["unit"], i["n"]))
        k = len(its)
        idx = sorted({round(j * (k - 1) / 4) for j in range(5)})
        j = 0
        while len(idx) < 5 and j < k:
            if j not in idx:
                idx.append(j)
            j += 1
        sample += [{"unit": its[i]["unit"], "n": its[i]["n"], "topic": t, "ref": its[i]["ref"],
                    "pid": pid_of(its[i]["ref_parsed"])} for i in sorted(idx)]
    json.dump(sample, open(os.path.join(WORK, "booklet_sample.json"), "w"), indent=0)
    print("sample", len(sample), "items;", "years", sorted(Counter(s["ref"].split()[1][:2] for s in sample).items()))
    print("papers:", " ".join(sorted({s["pid"] for s in sample})))


def margin_marks(doc, regions, tmp):
    """Marks '[n]' in the right margin of item regions (OCR at 300 dpi, whitelist)."""
    vals = []
    for p0, y0, y1 in regions:
        page = doc[p0]
        clip = pymupdf.Rect(470, y0, 590, y1)
        pm = page.get_pixmap(dpi=300, clip=clip, colorspace=pymupdf.csGRAY)
        f = os.path.join(tmp, "m.png")
        pm.save(f)
        r = subprocess.run(["tesseract", f, "-", "--psm", "11", "-c", "tessedit_char_whitelist=[]()|0123456789",
                            "-l", "eng"], capture_output=True, text=True, env=dict(os.environ, OMP_THREAD_LIMIT="1"))
        for m in re.finditer(r"[\[(|{]\s*(\d{1,2})\s*[\])|}]", r.stdout):
            v = int(m.group(1))
            if 0 < v <= 12:
                vals.append(v)
    return vals


def official_marks(qp_path, q, parts):
    sys.path.insert(0, os.path.dirname(__file__))
    from parse import load, parse_qp
    d = load(qp_path)
    qs = parse_qp(d)
    Q = next((x for x in qs if x["n"] == q), None)
    if Q is None:
        return None, None
    if not parts:
        return sum(m["value"] for m in Q["marks"]), Q["total"]
    want = []
    for g in re.finditer(r"([a-h])(?:\(([ivx,]+)\))?", parts):
        if g.group(2):
            want += [f"({g.group(1)})({r})" for r in g.group(2).split(",")]
        else:
            want.append(f"({g.group(1)})")
    tot = sum(m["value"] for m in Q["marks"] if any(m["label"].startswith(w) for w in want))
    return tot, Q["total"]


def marks():
    sample = json.load(open(os.path.join(WORK, "booklet_sample.json")))
    I = {(it["unit"], it["n"]): it for it in json.load(open(os.path.join(WORK, "booklet_items.json")))}
    man = json.load(open(os.path.join(WORK, "manifest_physics.json")))
    doc = pymupdf.open(SRC)
    res = []
    with tempfile.TemporaryDirectory() as tmp:
        for s in sample:
            it = I[(s["unit"], s["n"])]
            rp = it["ref_parsed"]
            mm = margin_marks(doc, it["regions"], tmp)
            ent = man.get(s["pid"], {})
            r = {"unit": s["unit"], "n": s["n"], "topic": s["topic"], "ref": it["ref"], "pid": s["pid"],
                 "printed": mm, "printed_sum": sum(mm)}
            if ent.get("qp", {}).get("status") != "ok":
                r["official"] = None
                r["issue"] = "official QP not available"
            else:
                try:
                    tot, qt = official_marks(os.path.join(ROOT, "data", ent["qp"]["file"]), rp["q"], rp["parts"])
                except Exception as e:
                    tot, qt = None, None
                    r["issue"] = f"QP parse error {e!r}"
                r["official"], r["official_q_total"] = tot, qt
            r["match"] = r.get("official") is not None and r["official"] == r["printed_sum"]
            res.append(r)
    json.dump(res, open(os.path.join(WORK, "booklet_marks.json"), "w"), indent=0)
    print("sampled", len(res), "marks match", sum(r["match"] for r in res),
          "no official", sum(r.get("official") is None for r in res))
    for r in res:
        if not r["match"]:
            print("  ", r["unit"], r["n"], r["ref"], "printed", r["printed"], "official", r.get("official"),
                  r.get("issue", ""))


if __name__ == "__main__":
    {"select": select, "marks": marks}[sys.argv[1]]()
