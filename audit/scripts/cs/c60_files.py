"""Check 10 FILES: every output file opens and is sound (qpdf --check), fonts are embedded, page
sizes are A4, no file is over 95 MB, the text layer is present on every body page, index.csv /
items.jsonl / topics.json parse and have the documented columns, git tracks every output."""
import csv, glob, json, subprocess
from collections import Counter
import pymupdf as f
from c00_common import *

F = []
rows = []
# fonts that the source papers themselves do not embed (the books inherit them unchanged)
src_ne = set()
for r in jl("sources.json"):
    if r["status"] != "OK":
        continue
    sd = f.open(os.path.join(DATA, r["file"]))
    for p in sd:
        for x in p.get_fonts(full=True):
            if x[1] == "n/a":
                src_ne.add(x[3])
for book in (1, 2):
    pdfs = [BOOKS[book]] + sorted(glob.glob(os.path.join(BOOKDIR[book], "units", "*.pdf")))
    for fn in pdfs:
        sz = os.path.getsize(fn)
        r = subprocess.run(["qpdf", "--check", fn], capture_output=True, text=True)
        ok = r.returncode == 0 and "No syntax or stream encoding errors" in r.stdout
        d = f.open(fn)
        fonts = Counter()
        notemb = set()
        for p in d:
            for x in p.get_fonts(full=True):
                fonts[x[3]] += 1
                if x[1] == "n/a" or (x[2] == "Type1" and not d.xref_get_key(x[0], "FontDescriptor")[1].endswith("R")):
                    notemb.add(x[3])
        sizes = Counter((round(p.rect.width), round(p.rect.height)) for p in d)
        notext = [p.number + 1 for p in d if len(p.get_text().split()) < 3]
        annots = sum(1 for p in d for _ in p.annots())
        row = {"file": os.path.relpath(fn, ROOT), "mb": round(sz / 1e6, 1), "pages": len(d), "qpdf_ok": ok, "sizes": dict((str(k), v) for k, v in sizes.items()),
               "not_embedded": sorted(notemb), "pages_without_text": notext[:10], "annots": annots, "encrypted": d.is_encrypted}
        rows.append(row)
        if not ok:
            F.append(("qpdf", row["file"], (r.stdout + r.stderr)[-200:]))
        if sz > 95e6:
            F.append(("over 95 MB", row["file"], row["mb"]))
        if set(sizes) != {(595, 842)}:
            F.append(("page size", row["file"], dict(sizes)))
        row["not_embedded_inherited"] = sorted(notemb & src_ne)
        own = [n for n in fonts if "Noto" in n or "Liberation" in n]
        row["own_fonts"] = sorted(own)
        if notemb - src_ne:
            F.append(("font not embedded (and not inherited from a source paper)", row["file"], sorted(notemb - src_ne)))
        if not own or any(n in notemb for n in own):
            F.append(("book font missing or not embedded", row["file"], own))
        if notext:
            F.append(("pages without text", row["file"], notext[:10]))
        if annots or d.is_encrypted:
            F.append(("annotations / encryption", row["file"]))
    idx = list(csv.DictReader(open(os.path.join(BOOKDIR[book], "index.csv"))))
    if list(idx[0]) != ["reference", "unit", "marks", "page", "also_topics", "context_parts", "sections", "answer_page", "insert"]:
        F.append(("index.csv columns", book, list(idx[0])))
    js = []
    for n, l in enumerate(open(os.path.join(BOOKDIR[book], "items.jsonl"))):
        try:
            js.append(json.loads(l))
        except Exception as e:
            F.append(("items.jsonl line does not parse", book, n + 1))
    keys = {"reference", "syllabus_code", "book", "unit", "unit_name", "sections", "learning_outcomes", "marks", "page",
            "answer_page", "also_units", "context_parts", "insert", "text", "answer_text"}
    if any(set(j) != keys for j in js):
        F.append(("items.jsonl keys", book))
    tp = json.load(open(os.path.join(BOOKDIR[book], "topics.json")))
    rows.append({"file": f"P{book} index.csv", "rows": len(idx)})
    rows.append({"file": f"P{book} items.jsonl", "rows": len(js)})
    rows.append({"file": f"P{book} topics.json", "rows": len(tp)})
big = subprocess.run("git ls-files -z | xargs -0 du -b 2>/dev/null | sort -rn | head -3", shell=True, capture_output=True, text=True, cwd=ROOT).stdout
jd({"files": rows, "fail": F, "largest_tracked": big, "fonts_not_embedded_in_sources": sorted(src_ne)}, "files.json", 1)
print("fonts the source papers do not embed:", sorted(src_ne))
print("files checked", len(rows), "| failures", len(F))
for r in rows:
    if "mb" in r:
        print("  ", r["file"][-58:], r["mb"], "MB", r["pages"], "p", "qpdf ok" if r["qpdf_ok"] else "QPDF FAIL")
for x in F:
    print("  FAIL", str(x)[:300])
