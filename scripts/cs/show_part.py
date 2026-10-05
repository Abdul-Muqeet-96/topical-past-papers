"""Print the full question text and mark-scheme text of given parts.
usage: show_part.py phase pid:Q:key [pid:Q:key ...] [--ms N]   (key as in the tags file, e.g. b.ii or Q)"""
import os, re, sys
import pymupdf
sys.path.insert(0, os.path.dirname(__file__))
from paths import DATA, work, jload
from tags import key2lab
from items import unit_text, _L
from parse import load

args = [a for a in sys.argv[1:] if not a.startswith("--") and not a.isdigit()]
nms = int(sys.argv[sys.argv.index("--ms") + 1]) if "--ms" in sys.argv else 350
P = jload(work(f"parts_{args[0]}.json"))
docs = {}
for spec in args[1:]:
    pid, q, key = spec.split(":")
    p = P[pid]
    Q = next(x for x in p["questions"] if x["n"] == int(q))
    lab = key2lab(key)
    L = _L(Q, lab)
    rows = L["ms_rows"] if lab == L["label"] else next(R for R in L["romans"] if R["label"] == lab)["ms_rows"]
    if p["ms"] not in docs:
        docs[p["ms"]] = load(os.path.join(DATA, p["ms"]))
    md = docs[p["ms"]]
    ms = " ".join(md[pg].get_text("text", clip=pymupdf.Rect(rc)) for r in rows for pg, rc in r["segs"])
    t = re.sub(r"[.…]{4,}", "…", unit_text(Q, lab) or "")
    print(f"## {spec} [{p['ref']}]\nSTEM: {Q['stem_text'][:300]}\nQ: {t[:700]}\nMS: {re.sub(r'\s+', ' ', ms)[:nms]}\n")
