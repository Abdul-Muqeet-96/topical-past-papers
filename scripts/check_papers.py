"""Stage 3: paper-level verification for every downloaded paper of a phase.
Writes work/checks_<phase>.json; prints counts only."""
import json, os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(__file__))
import parse
from parse import load, parse_qp, ms_rows, paper_ref, fix_ms_rows

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAME = {"m": "MAR", "s": "M/J", "w": "O/N"}


def check(pid, ent):
    qd = load(os.path.join(ROOT, "data", ent["qp"]["file"]))
    md = load(os.path.join(ROOT, "data", ent["ms"]["file"]))
    ref = paper_ref(qd)
    res = {"pid": pid, "ref": ref, "paper_excluded": None, "questions": {}, "issues": []}
    exp = f"{SNAME[ent['series']]} {ent['year'] % 100:02d}/P{ent['variant']}"
    if ref != exp:
        res["paper_excluded"] = f"reference from header '{ref}' != expected '{exp}'"
        return res
    if ref != paper_ref(md):
        res["paper_excluded"] = f"MS header reference '{paper_ref(md)}' != QP '{ref}'"
        return res
    qs = parse_qp(qd)
    parse.MS_TYPOS.clear()
    rows = ms_rows(md)
    res["ms_label_fixes"] = [[a, b] for a, b in parse.MS_TYPOS] + \
        [[o, n] for _, o, n in fix_ms_rows(rows, qs)]
    nums = [q["n"] for q in qs]
    # 1. every question once (parser only accepts sequential numbers; check vs MS)
    if not nums:
        res["paper_excluded"] = "no questions found in QP text layer"
        return res
    # (QP numbers are accepted only in sequence 1,2,3..., so each appears once.)
    extra = sorted({r["q"] for r in rows} - set(nums))
    if extra:
        res["paper_excluded"] = f"MS has questions {extra} not in QP {nums}"
        return res
    if any(q.get("total_dup") for q in qs):
        res["paper_excluded"] = "a question has more than one [Total]"
        return res
    totals = [q["total"] for q in qs]
    if None in totals:
        res["paper_excluded"] = f"missing [Total] in Q{[q['n'] for q in qs if q['total'] is None]}"
        return res
    # 3. totals sum to 60
    if sum(totals) != 60:
        res["paper_excluded"] = f"question totals sum to {sum(totals)}, not 60"
        return res
    msq = Counter()
    for r in rows:
        msq[r["q"]] += r["mark_total"]
    for q in qs:
        ps = sum(m["value"] for m in q["marks"])
        st = {"total": q["total"], "part_sum": ps, "ms": msq[q["n"]], "ok": True, "why": ""}
        if ps != q["total"]:
            st.update(ok=False, why=f"part marks sum {ps} != [Total: {q['total']}]")
        elif msq[q["n"]] != q["total"]:
            st.update(ok=False, why=f"MS marks {msq[q['n']]} != QP total {q['total']}")
        res["questions"][q["n"]] = st
    return res


def main():
    phase = sys.argv[1]
    man = json.load(open(os.path.join(ROOT, "data", "manifest.json")))
    out = {}
    for pid, ent in sorted(man.items()):
        if ent["phase"] != phase or ent["status"] != "ok":
            continue
        try:
            out[pid] = check(pid, ent)
        except Exception as e:  # unreadable -> exclude, report
            out[pid] = {"pid": pid, "ref": None, "paper_excluded": f"parse error: {e!r}", "questions": {}}
    os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, "work", f"checks_{phase}.json"), "w"), indent=1)
    exc = [p for p, r in out.items() if r["paper_excluded"]]
    badq = [(p, n) for p, r in out.items() if not r["paper_excluded"]
            for n, q in r["questions"].items() if not q["ok"]]
    print(f"{phase}: papers checked {len(out)}, excluded {len(exc)}, questions excluded {len(badq)}")
    for p in exc:
        print("  X", p, out[p]["paper_excluded"])
    for p, n in badq:
        print("  q", p, n, out[p]["questions"][n]["why"])


if __name__ == "__main__":
    main()
