"""Check 2/3: the independent QP and MS parses against each other and against the build.
 a. question numbers 1..n once each; margin marks add up to the cover total; [Total] where printed;
 b. per leaf: QP marks = MS marks (independent parsers on both sides);
 c. the build's parts (λ-cs/work/parts_*.json): same questions, same leaves, same marks;
 d. the build's question exclusions (checks_*.json) against the independent result."""
import json, re, sys
from collections import Counter, defaultdict
from c00_common import *

QP, MS = jl("qp_parse.json"), jl("ms_parse.json")
out = {"paper": {}, "leaf_mismatch": [], "build_diff": [], "q_mismatch": []}
P, CH = {}, {}
for ph in ("phase1", "phase2"):
    P.update(json.load(open(os.path.join(CS, "work", f"parts_{ph}.json"))))
    CH.update(json.load(open(os.path.join(CS, "work", f"checks_{ph}.json"))))
n_leaf = n_ok = 0
for k in sorted(QP):
    if k not in MS:
        continue
    q, m = QP[k], MS[k]
    marks = {int(a): dict(b) for a, b in q["parts"].items()}
    used_inner = False
    g = sum(sum(x.values()) for x in marks.values())
    if g != q["cover"] and g + sum(i[1] for x in q["inner"].values() for i in x) == q["cover"]:
        for qq, x in q["inner"].items():
            for key, v, pg, y, x1 in x:
                marks[int(qq)][key] = marks[int(qq)].get(key, 0) + v
        used_inner = True
        g = q["cover"]
    seq_ok = q["qnums"] == list(range(1, len(q["qnums"]) + 1))
    tot_ok = all(len(t) == 1 and t[0] == sum(marks[int(a)].values()) for a, t in q["totals"].items())
    out["paper"][k] = {"seq_ok": seq_ok, "sum": g, "cover": q["cover"], "tot_ok": tot_ok, "used_inner": used_inner,
                       "layout": m["layout"]}
    # MS marks per label
    msm = defaultdict(int)
    msq = defaultdict(int)
    seen_rep = set()
    for i, r in enumerate(m["rows"]):
        v = sum(x[0] for x in r["marks"])
        if m["layout"] == "text" and r.get("max"):
            # 'max n' is the value of the part, whatever the [1]s of its marking points add up to;
            # the same max printed again under an alternative solution counts once
            mx = [x[0] for x in r["max"]]
            v = mx[0] if len(set(mx)) == 1 else sum(mx)
        if m["layout"] == "table" and i and m["rows"][i - 1]["label"] == r["label"] and r["page"] > m["rows"][i - 1]["page"] \
                and [x[0] for x in r["marks"]] == [x[0] for x in m["rows"][i - 1]["marks"]] and r["marks"]:
            out.setdefault("repeated_rows", []).append({"paper": k, "label": r["label"], "page": r["page"], "marks": v})
            v = 0      # the same label and mark printed again on the next page (continuation / alternative)
        msm[r["label"]] += v
        msq[r["q"]] += v
    # an MS that labels one level deeper than the QP, or with the question number alone
    deeper = defaultdict(int)
    for lab, v in msm.items():
        deeper[lab.rsplit("(", 1)[0]] += v if "(" in lab else 0
    for qq in sorted(marks):
        qs = sum(marks[qq].values())
        if msq.get(qq, 0) != qs:
            out["q_mismatch"].append({"paper": k, "q": qq, "qp": qs, "ms": msq.get(qq, 0), "layout": m["layout"],
                                      "qp_leaves": marks[qq], "ms_leaves": {a: b for a, b in msm.items() if a.split("(")[0] == str(qq)}})
        for leaf, v in marks[qq].items():
            n_leaf += 1
            if msm.get(leaf) == v:
                n_ok += 1
            elif leaf not in msm and deeper.get(leaf) == v:
                n_ok += 1
                out.setdefault("label_depth", []).append({"paper": k, "leaf": leaf, "ms_labels": sorted(a for a in msm if a.startswith(leaf + "("))})
            else:
                out["leaf_mismatch"].append({"paper": k, "leaf": leaf, "qp": v, "ms": msm.get(leaf), "layout": m["layout"]})
    # against the build
    if k in P:
        bq = {x["n"]: x for x in P[k]["questions"]}
        exc = {int(a) for a, b in CH[k]["questions"].items() if not b["ok"]}
        for qq in sorted(set(marks) | set(bq)):
            if qq not in bq:
                if qq not in exc:
                    out["build_diff"].append({"paper": k, "q": qq, "why": "question not in the build's parts and not excluded"})
                continue
            if qq not in marks:
                out["build_diff"].append({"paper": k, "q": qq, "why": "question in the build, not found by the audit parser"})
                continue
            bl = {}
            Qb = bq[qq]
            for lt in Qb["letters"]:
                for sub in (lt.get("romans") or [lt]):
                    lab = f"{qq}{sub['label'] or ''}"
                    bl[lab] = sub.get("marks")
            if bl != marks[qq]:
                out["build_diff"].append({"paper": k, "q": qq, "why": "leaves/marks differ", "build": bl, "audit": marks[qq]})
    elif CH.get(k, {}).get("paper_excluded") is None and k in CH:
        out["build_diff"].append({"paper": k, "why": "paper passed the checks but has no parts"})
jd(out, "compare.json", 1)
pp = out["paper"]
print("papers with QP+MS:", len(pp), "| sequence ok", sum(v["seq_ok"] for v in pp.values()), "| sum = cover = 75",
      sum(v["sum"] == v["cover"] == 75 for v in pp.values()), "| [Total] ok", sum(v["tot_ok"] for v in pp.values()),
      "| needed marks short of the margin", sum(v["used_inner"] for v in pp.values()))
print("leaves", n_leaf, "QP=MS", n_ok, "| leaf mismatches", len(out["leaf_mismatch"]), Counter(x["layout"] for x in out["leaf_mismatch"]))
print("question-level QP!=MS:", len(out["q_mismatch"]), Counter(x["layout"] for x in out["q_mismatch"]))
print("build differences:", len(out["build_diff"]), "| repeated continuation rows counted once", len(out.get("repeated_rows", [])),
      "| MS labelled one level deeper than the QP", len(out.get("label_depth", [])))
# every remaining difference must be one the build knows about: the question is excluded
# (checks_*.json) or the MS label was read as another label and logged (ms_label_fixes)
unexpl = []
for x in out["leaf_mismatch"]:
    c = CH[x["paper"]]
    qn = x["leaf"].split("(")[0]
    if not c["questions"][qn]["ok"]:
        x["explained"] = "question excluded by the build: " + c["questions"][qn]["why"]
    elif any(b.split("(")[0] == qn for a, b in c.get("ms_label_fixes", [])):
        x["explained"] = "MS label slip logged by the build: " + str([f for f in c["ms_label_fixes"] if f[1].split("(")[0] == qn])
    else:
        unexpl.append(x)
exq = {(k, int(a)) for k, c in CH.items() for a, b in c["questions"].items() if not b["ok"]}
mism = {(x["paper"], x["q"]) for x in out["q_mismatch"]}
out["excluded_not_confirmed"] = sorted(exq - mism)
out["unexplained"] = unexpl
jd(out, "compare.json", 1)
print("leaf differences explained (excluded question / logged label slip):", len(out["leaf_mismatch"]) - len(unexpl), "| unexplained:", len(unexpl))
for x in unexpl:
    print("   UNEXPLAINED", x)
print("questions excluded by the build:", len(exq), "| of these the audit parsers also find QP != MS:", len(exq & mism),
      "| not confirmed:", sorted(exq - mism), "| QP != MS but not excluded:", sorted(mism - exq))
