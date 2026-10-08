"""Check 1 SOURCE. For every paper the run was told to try: is the file in data/, and does page 1,
read independently, show the code/variant, the paper number and title, the series and the right
document type? Also asks the site again about every file the run recorded as not on the site."""
import os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import pymupdf as f
from c00_common import *

SN = {"m": ("February/March", "March"), "s": ("May/June", "June"), "w": ("October/November", "November")}


def head(fn, code, s, y, v, kind):
    r = {}
    try:
        d = f.open(fn)
        d[0]
    except Exception as e:
        return {"status": "UNREADABLE", "error": str(e)[:60]}
    t = re.sub(r"[‐‑‒–—]", "-", re.sub(r"\s+", " ", d[0].get_text()))
    pn = v // 10
    r["pages"] = len(d)
    r["code_ok"] = f"{code}/{v}" in t
    r["paper_no"] = re.findall(r"\bPaper (\d)\b", t)
    r["paper_ok"] = r["paper_no"][:1] == [str(pn)]
    full = {1: "Theory Fundamentals", 2: "Fundamental Problem-solving and Programming Skills"}[pn]
    r["title"] = "full" if full.lower() in t.lower() else (
        "written paper" if re.search(r"Written Paper", t) else
        "problem solving & programming" if re.search(r"Problem[- ]Solving (&|and) Programming", t, re.I) else "none")
    r["series_ok"] = any(f"{n} 20{y:02d}" in t for n in SN[s])
    # the document type as printed in capitals on the cover ("MARK SCHEME", "INSERT"); a question
    # paper only mentions "Insert (enclosed)" / "the insert" in lower case
    r["type"] = "ms" if "MARK SCHEME" in t.upper() else ("in" if re.search(r"\bINSERT\b", t) else "qp")
    r["type_ok"] = r["type"] == kind
    r["status"] = "OK" if (r["code_ok"] and r["paper_ok"] and r["series_ok"] and r["type_ok"]) else "HEADER_MISMATCH"
    return r


def probe(fn):
    c = subprocess.run(["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}", "-r", "0-1023", "--max-time", "60",
                        URL + fn], capture_output=True, text=True).stdout.strip()
    return fn, c


rows = []
for code, s, y, v in expected():
    for kind in ("qp", "ms", "in"):
        fn = f"{code}_{s}{y:02d}_{kind}_{v}.pdf"
        r = {"file": fn, "pid": pid(code, s, y, v), "kind": kind}
        p = os.path.join(DATA, fn)
        if not os.path.exists(p):
            r["status"] = "ABSENT"
        else:
            r.update(head(p, code, s, y, v, kind))
        rows.append(r)
if "--probe" in sys.argv:
    absent = [r["file"] for r in rows if r["status"] == "ABSENT" and r["kind"] != "in"]
    with ThreadPoolExecutor(4) as ex:
        codes = dict(ex.map(probe, absent))
    for r in rows:
        if r["file"] in codes:
            r["http_now"] = codes[r["file"]]
jd(rows, "sources.json", 0)
c = Counter((r["kind"], r["status"]) for r in rows)
print("files expected", len(rows), dict(c))
print("titles:", Counter((r["kind"], r.get("title")) for r in rows if r["status"] not in ("ABSENT", "UNREADABLE")))
for r in rows:
    if r["status"] in ("HEADER_MISMATCH", "UNREADABLE"):
        print(" ", r["file"], r["status"], {k: r.get(k) for k in ("code_ok", "paper_no", "series_ok", "type", "error")})
if "--probe" in sys.argv:
    print("site answers now for absent QP/MS:", Counter(r.get("http_now") for r in rows if "http_now" in r))
    print("  absent files that the site now serves (HTTP 200/206):",
          [r["file"] for r in rows if r.get("http_now") in ("200", "206")])
extra = sorted(set(x for x in os.listdir(DATA) if x.endswith(".pdf")) - {r["file"] for r in rows})
print("unexpected extra files in data/:", extra)
