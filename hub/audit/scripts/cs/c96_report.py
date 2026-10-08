"""Check REPORT ACCURACY: the figures printed in λ-cs/reports/SUMMARY.md and λ-cs/reports/report.md against the
audit's own counts (book pages read back from the PDFs, index.csv, the audit's paper parsers).
Writes report_accuracy.json: one row per figure compared, with ok true/false."""
import csv, json, re
from collections import Counter, defaultdict
from c00_common import *
import pymupdf as f

rows = []


def cmp(what, printed, counted):
    rows.append({"what": what, "printed": printed, "counted": counted, "ok": printed == counted})


S = open(os.path.join(CS, "reports", "SUMMARY.md")).read()
R = open(os.path.join(CS, "reports", "report.md")).read()


def table(title):
    """rows of the markdown table under a heading that starts with title: [[cell, ...], ...]"""
    m = re.search(r"^## " + re.escape(title) + r".*?\n\n((?:\|.*\n)+)", S, re.M)
    out = []
    for ln in m.group(1).strip().split("\n")[2:]:
        out.append([c.strip().strip("*") for c in ln.strip().strip("|").split("|")])
    return out


# ---- Papers table
src = jl("sources.json")
by = defaultdict(dict)
for s in src:
    by[s["pid"]][s["kind"]] = s["status"]
ph = lambda pid: 0 if pid.startswith("9618") else 1
att, absent, ok, ins = [0, 0], [0, 0], [0, 0], [0, 0]
for pid, k in by.items():
    if "qp" not in k:
        continue
    att[ph(pid)] += 1
    if k["qp"] == "ABSENT" or k.get("ms") == "ABSENT":      # a paper needs both files
        absent[ph(pid)] += 1
    if k["qp"] == "OK" and k.get("ms") == "OK":
        ok[ph(pid)] += 1
for s in src:
    if s["kind"] == "in" and s["status"] == "OK":
        ins[ph(s["pid"])] += 1
cmpd = jl("compare.json")
qx = [0, 0]
for q in cmpd["q_mismatch"]:
    qx[ph(q["pid"] if "pid" in q else q["paper"])] += 1
P = {r[0]: r[1:] for r in table("Papers")}
num = lambda x: int(re.sub(r"[^\d]", "", x) or 0)
for label, val in (("Papers attempted", att), ("Not on the site", absent), ("Downloaded and header-verified (QP + MS)", ok),
                   ("Inserts found", ins), ("Questions excluded (MS marks ≠ QP marks)", qx)):
    cmp(f"SUMMARY Papers: {label}", [num(x) for x in P[label][:2]], val)
    cmp(f"SUMMARY Papers: {label} (total)", num(P[label][2]), sum(val))

# ---- per unit tables, from the books themselves
tot_items = tot_marks = 0
phase_items, phase_marks = [0, 0], [0, 0]
for book, title in ((1, "Paper 1 book"), (2, "Paper 2 book")):
    bp = jl(f"book_parse_p{book}.json")
    idx = list(csv.DictReader(open(os.path.join(BOOKDIR[book], "index.csv"))))
    marks = {r["reference"]: int(r["marks"]) for r in idx}
    per = defaultdict(lambda: [set(), 0, 0])
    allp = set()
    for it in bp["items"]:
        if it["side"] != "Q":
            continue
        pidk = ref_key(it["ref"])[0]
        u = per[it["unit"]]
        u[0].add(pidk)
        u[1] += 1
        u[2] += marks[it["ref"]]
        allp.add(pidk)
        phase_items[ph(pidk)] += 1
        phase_marks[ph(pidk)] += marks[it["ref"]]
    T = table(title)
    for r in T:
        if r[0] == "Total":
            cmp(f"SUMMARY {title}: total papers/items/marks", [num(x) for x in r[1:4]],
                [len(allp), sum(v[1] for v in per.values()), sum(v[2] for v in per.values())])
        else:
            u = int(r[0].split()[0])
            cmp(f"SUMMARY {title}: unit {u} papers/items/marks", [num(x) for x in r[1:4]], [len(per[u][0]), per[u][1], per[u][2]])
    tot_items += sum(v[1] for v in per.values())
    tot_marks += sum(v[2] for v in per.values())
    # cover figures of the book
    st = jl("structure.json")[f"P{book}"]
    if "cover" in st:
        cmp(f"cover of the P{book} book: items, marks", [st["cover"]["items"], st["cover"]["marks"]],
            [sum(v[1] for v in per.values()), sum(v[2] for v in per.values())])
cmp("SUMMARY Papers: Items in the books", [num(x) for x in P["Items in the books"]], phase_items + [tot_items])
cmp("SUMMARY Papers: Marks in the books", [num(x) for x in P["Marks in the books"]], phase_marks + [tot_marks])

# ---- files table: pages and sizes
for m in re.finditer(r"^\| (λ-cs/\S+?)(?: \((\d+) pages\))? \| ([\d.]+) (MB|KB) \|", S, re.M):
    path = os.path.join(ROOT, m.group(1))
    if not os.path.exists(path):
        cmp(f"file listed in SUMMARY exists: {m.group(1)}", True, False)
        continue
    n = os.path.getsize(path)
    printed = float(m.group(3)) * (1e6 if m.group(4) == "MB" else 1e3)
    if path.endswith("SUMMARY.md") or path.endswith("report.md"):
        continue                       # written after the table was printed
    cmp(f"size of {os.path.basename(path)}", True, abs(printed - n) <= max(0.06e6 if m.group(4) == "MB" else 600, 0.02 * n))
    if m.group(2):
        cmp(f"pages of {os.path.basename(path)}", int(m.group(2)), len(f.open(path)))
listed = set(m.group(1) for m in re.finditer(r"^\| (λ-cs/\S+?)(?: \(\d+ pages\))? \|", S, re.M))
for book in (1, 2):
    for dp, _, fs in os.walk(BOOKDIR[book]):
        for fn in fs:
            rel = os.path.relpath(os.path.join(dp, fn), ROOT)
            cmp(f"output file listed in SUMMARY: {rel}", True, rel in listed)

# ---- report.md
cov = jl("coverage.json")
cmp("report.md: exclusion rows that match no part of a verified paper", 0, len(cov["stale_report_rows"]))
cmp("report.md: parts listed as excluded but present in a book", 0, len(cov["listed_and_included"]))
auto = json.load(open(os.path.join(CS, "build", "work", "auto_decided.json")))
sec = R.split("## AUTO-DECIDED")[1].split("\n## ")[0]
cmp("report.md AUTO-DECIDED: every hand-kept decision row is printed", len(auto), sum(1 for a in auto if f"| {a['item']} |" in sec))
m = re.search(r"Stages finished: ([\d, ]+)", S)
state = json.load(open(os.path.join(CS, "build", "state_cs.json")))
done = sorted(int(k) for k, v in state["stages"].items() if v == "done")
cmp("SUMMARY: stages finished = state_cs.json", [int(x) for x in m.group(1).replace(" ", "").split(",") if x], done)
jd(rows, "report_accuracy.json", 0)
bad = [r for r in rows if not r["ok"]]
print("figures compared:", len(rows), "| wrong:", len(bad))
for r in bad:
    print("  ", r["what"], "printed", r["printed"], "counted", r["counted"])
