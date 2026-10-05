"""Stage 2: paper-level verification for every downloaded paper of a phase
(λ-cs/CLAUDE-cs.md, "Paper-level verification").

1. every question number appears exactly once;
2. the part [marks] add up to the paper total printed on the cover; a printed
   [Total: n] must match its question;
3. the MS marks of each question equal the QP marks of that question;
4. the reference comes from the header text only.

Writes λ-cs/work/checks_<phase>.json; prints counts only."""
import os, re, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(__file__))
import parse
from parse import load, parse_qp, ms_rows_any, paper_ref, fix_ms_rows, cover_total, special_page, page_lines
from paths import DATA, MANIFEST, SERIES_REF, PAPER_TOTAL, work, jload, jdump


def margin_numbers(doc):
    """Independent count for check 1: every number printed at the question-number
    position (left margin, start of a line), in page order."""
    out = []
    for pno in range(1, doc.page_count):
        if special_page(doc[pno]):
            continue
        for ws in page_lines(doc[pno]):
            w = ws[0]
            if re.fullmatch(r"[1-9]\d?", w[4]) and w[0] < 64 and not parse._mono_word(doc[pno], w):
                out.append(int(w[4]))
    return out


def check(pid, ent):
    qd = load(os.path.join(DATA, ent["qp"]["file"]))
    md = load(os.path.join(DATA, ent["ms"]["file"]))
    ref = paper_ref(qd)
    res = {"pid": pid, "ref": ref, "paper_excluded": None, "questions": {}, "issues": []}
    exp = f"{SERIES_REF[ent['series']]} {ent['year'] % 100:02d}/P{ent['variant']}"
    if ref != exp:
        res["paper_excluded"] = f"reference from header '{ref}' != expected '{exp}'"
        return res
    if ref != paper_ref(md):
        res["paper_excluded"] = f"MS header reference '{paper_ref(md)}' != QP '{ref}'"
        return res
    # AUTO-DECIDED: in 2021 both syllabuses sat papers with the same series and
    # variant; a 9608 reference then carries the code so that references stay unique
    twin = f"9618_{ent['series']}{ent['year'] % 100:02d}_{ent['variant']}"
    if ent["code"] == "9608" and MAN.get(twin, {}).get("status") == "ok":
        ref = res["ref"] = "9608 " + ref
        res["ref_prefixed"] = True
    qs = parse_qp(qd)
    if getattr(qd, "_marks2_used", None):
        res["issues"].append(f"{len(qd._marks2_used)} mark(s) printed short of the right-hand margin were needed "
                             f"to reach the cover total and are counted")
    parse.MS_TYPOS.clear()
    parse.APX_NOTES.clear()
    rows = ms_rows_any(md, qs)
    apx = getattr(md, "_apx", (0, []))
    if apx[0] or apx[1] or parse.APX_NOTES:
        res["ms_appendix"] = {"attached": apx[0], "unattached": apx[1], "notes": list(parse.APX_NOTES)}
    if rows and rows[0].get("text_layout"):
        res["ms_text_layout"] = True
    res["ms_label_fixes"] = [[a, b] for a, b in parse.MS_TYPOS] + \
        [[o, n] for _, o, n in fix_ms_rows(rows, qs) if o != n]
    # an MS row labelled one level deeper than the question paper goes ('5(a)(i)' where 5(a) has no
    # sub-parts) is the answer of that part; logged, nothing is changed
    for q in qs:
        leaves = {m["label"] for m in q["marks"]}
        for r in rows:
            if r["q"] == q["n"] and r["part"] and r["part"] not in leaves:
                up = [l for l in leaves if l and r["part"].startswith(l)]
                if up:
                    res.setdefault("ms_label_notes", []).append([r["label"], f"{q['n']}{up[0]}"])
    nums = [q["n"] for q in qs]
    if not nums:
        res["paper_excluded"] = "no questions found in QP text layer"
        return res
    # 1. every question number exactly once. The parser accepts numbers only in
    # the sequence 1, 2, 3 ...; the margin numbers and the MS must agree with it.
    seen = Counter(n for n in margin_numbers(qd) if n <= max(nums) + 3)
    missing = [n for n in range(1, max(nums) + 1) if n not in nums]
    beyond = sorted(n for n in seen if n > max(nums))
    msq_set = {r["q"] for r in rows}
    extra = sorted(msq_set - set(nums))
    res["question_numbers"] = nums
    if missing:
        res["paper_excluded"] = f"question numbers missing: {missing}"
        return res
    if extra:
        res["paper_excluded"] = f"MS has questions {extra} not in QP {nums}"
        return res
    if beyond and any(n == max(nums) + 1 for n in beyond) and (max(nums) + 1) in msq_set:
        res["paper_excluded"] = f"a question after Q{max(nums)} was not read"
        return res
    if any(q.get("total_dup") for q in qs):
        res["paper_excluded"] = "a question has more than one [Total]"
        return res
    # 2. part marks add up to the cover total
    cov = cover_total(qd)
    res["cover_total"] = cov
    if cov != PAPER_TOTAL:
        res["issues"].append(f"cover total reads {cov}")
    part_sum = sum(m["value"] for q in qs for m in q["marks"])
    res["part_sum"] = part_sum
    if cov is None or part_sum != cov:
        res["paper_excluded"] = f"part marks sum to {part_sum}, cover total is {cov}"
        return res
    ms_cov = cover_total(md)
    if ms_cov is not None and ms_cov != cov:
        res["issues"].append(f"MS maximum mark {ms_cov} != QP total {cov}")
    # paper-wide note that the insert / appendix is to be used
    t1 = " ".join(parse.norm_text(qd[p].get_text()) for p in range(1, min(qd.page_count, 3)))
    res["insert_line"] = bool(re.search(r"Refer to the insert", t1, re.I))
    msq = Counter()
    for r in rows:
        msq[r["q"]] += r["mark_total"]
    for q in qs:
        ps = sum(m["value"] for m in q["marks"])
        st = {"total": q["total"], "part_sum": ps, "ms": msq[q["n"]], "ok": True, "why": ""}
        if q["total"] is not None and ps != q["total"]:
            st.update(ok=False, why=f"part marks sum {ps} != [Total: {q['total']}]")
        elif msq[q["n"]] != ps:
            st.update(ok=False, why=f"MS marks {msq[q['n']]} != QP marks {ps}")
        res["questions"][q["n"]] = st
    return res


MAN = {}


def main():
    phase = sys.argv[1]
    man = jload(MANIFEST)
    MAN.update(man)
    out = {}
    for pid, ent in sorted(man.items()):
        if ent["phase"] != phase or ent["status"] != "ok":
            continue
        try:
            out[pid] = check(pid, ent)
        except Exception as e:  # unreadable -> exclude, report
            out[pid] = {"pid": pid, "ref": None, "paper_excluded": f"parse error: {e!r}", "questions": {}}
    jdump(out, work(f"checks_{phase}.json"))
    exc = [p for p, r in out.items() if r["paper_excluded"]]
    badq = [(p, n) for p, r in out.items() if not r["paper_excluded"]
            for n, q in r["questions"].items() if not q["ok"]]
    nq = sum(len(r["questions"]) for r in out.values())
    print(f"{phase}: papers checked {len(out)}, excluded {len(exc)}, questions {nq}, questions excluded {len(badq)}, "
          f"MS label fixes {sum(len(r.get('ms_label_fixes', [])) for r in out.values())}")
    for p in exc:
        print("  X", p, out[p]["paper_excluded"])
    for p, n in badq:
        print("  q", p, n, out[p]["questions"][n]["why"])
    for p, r in out.items():
        for i in r.get("issues", []):
            print("  !", p, i)


if __name__ == "__main__":
    main()
