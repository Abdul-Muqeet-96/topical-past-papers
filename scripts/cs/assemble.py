"""Stage 3/4: tag leaves with syllabus learning outcomes and assemble items.

Usage: python3 scripts/cs/assemble.py phase1|phase2
Reads work/parts_<phase>.json + work/tags_<phase>.txt.
Writes work/items_<phase>.json, work/topics_<phase>.json, work/log_<phase>.json.

A tag is a learning-outcome id from work/syllabus.json ("1.2.3" = unit 1,
section 1.2, third outcome), "X" (no clear match in the 2027-29 syllabus) or
"PR" (needs pre-release material). An item is filed by its unit: units 1-8 go
to the Paper 1 book, units 9-12 to the Paper 2 book, whatever paper it is from.
"""
import json, os, re, sys
from collections import defaultdict, OrderedDict
sys.path.insert(0, os.path.dirname(__file__))
from items import resolve, marks, find_letter, letter_of, unit_region, _order_key, _L
from tags import load as load_tags
from parse import load
from crops import bands
from layout import Flow
from paths import DATA, SERIES_ORDER, work, jload, jdump
import inserts

SYL = jload(work("syllabus.json"))
TOPICS = OrderedDict((int(k), v) for k, v in SYL["units"].items())
SECTIONS = dict(SYL["sections"])
LOS = SYL["los"]
MAX_CTX_H = 744        # one page of the book ("about one page")
EXCLUDE_CODES = {"X": "no clear match in the 2027-29 learning outcomes",
                 "PR": "needs the pre-release material (not part of the paper)"}


def book_of(unit):
    return 1 if unit <= 8 else 2


def section_of(code):
    return ".".join(code.split(".")[:2])


def topic_of(code):
    return None if code in EXCLUDE_CODES else int(code.split(".")[0])


ROMAN_ONLY = set()     # (paper ref, question) whose sub-parts are romans directly under the question


def register_roman_only(P):
    for p in P.values():
        for Q in p["questions"]:
            if Q["letters"] and Q["letters"][0]["letter"] is None and Q["letters"][0]["romans"]:
                ROMAN_ONLY.add((p["ref"], Q["n"]))


def ref_units(paper_ref, q, units):
    """Reference in the Physics-booklet style (audit A-027, decision D1):
    Q5/b, Q5/b(ii), Q3/b(ii,iii), Q3/a,b,c, Q6/a,b(i,ii,iii). A question whose
    sub-parts are romans with no letter: Q4/(i), Q4/(iii,iv)."""
    groups = []          # [letter, [romans]] in paper order
    ro = (paper_ref, q) in ROMAN_ONLY
    for u in units:
        lab = u.replace("#intro", "")
        m = None if ro else re.match(r"\(([a-z])\)(?:\(([ivx]+)\))?$", lab)
        if not m:
            m2 = re.match(r"\(([ivx]+)\)$", lab)
            letter, roman = (None, m2.group(1)) if m2 else (None, None)
        else:
            letter, roman = m.group(1), m.group(2)
        if groups and groups[-1][0] == letter and roman:
            groups[-1][1].append(roman)
        else:
            groups.append([letter, [roman] if roman else []])
    parts = [(g[0] or "") + (f"({','.join(g[1])})" if g[1] else "") for g in groups]
    parts = [p for p in parts if p]
    return f"{paper_ref}/Q{q}" + ("/" + ",".join(parts) if parts else "")


class Ctx:
    """Caches open PDFs and computes crop heights."""
    def __init__(self):
        self.docs = {}

    def doc(self, f):
        if f not in self.docs:
            self.docs[f] = load(os.path.join(DATA, f))
        return self.docs[f]

    def height(self, doc, region):
        return Flow.bands_height(bands(doc, region), 1.0) if region else 0


def leaf_info(Q, L, T, pid):
    out = []
    if L["romans"]:
        for R in L["romans"]:
            out.append((R["label"], T[(pid, Q["n"], R["label"])], R["marks"]))
    else:
        out.append((L["label"], T[(pid, Q["n"], L["label"])], L["marks"]))
    return out


def majority(leaves):
    """Topic with most marks; tie -> topic of first sub-part (flag)."""
    by = defaultdict(int)
    for lab, code, mk in leaves:
        by[topic_of(code)] += mk
    best = max(by.values())
    tops = [t for t, v in by.items() if v == best]
    if len(tops) == 1:
        return tops[0], dict(by), False
    first = next(topic_of(c) for _, c, _ in leaves if topic_of(c) in tops)
    return first, dict(by), True


def assemble(phase):
    P = jload(work(f"parts_{phase}.json"))
    register_roman_only(P)
    T = load_tags(phase)
    cx = Ctx()
    ins = inserts.Inserts()
    items, topics, log = [], [], defaultdict(list)
    for pid, p in sorted(P.items()):
        qd = cx.doc(p["qp"])
        for Q in p["questions"]:
            units = []   # (units list, topic, by-topic marks, flags)
            for L in Q["letters"]:
                lv = leaf_info(Q, L, T, pid)
                for lab, code, mk in lv:
                    lo = LOS.get(code)
                    topics.append({"ref": ref_units(p['ref'], Q['n'], [lab]), "paper": pid, "q": Q["n"], "part": lab,
                                   "unit": topic_of(code), "section": section_of(code) if lo else None,
                                   "lo": code if lo else None,
                                   "justification": (f"{section_of(code)} {SECTIONS[section_of(code)]}: {lo['text']}"
                                                     if lo else EXCLUDE_CODES.get(code, "no clear syllabus match")),
                                   "marks": mk, "code": code})
                xs = [l for l, c, _ in lv if c in EXCLUDE_CODES]
                if xs and (len(xs) == len(lv) or not L["romans"]):
                    kinds = {c for _, c, _ in lv if c in EXCLUDE_CODES}
                    key = "pre_release" if kinds == {"PR"} else "out_of_syllabus"
                    log[key].append({"ref": ref_units(p['ref'], Q['n'], [L['label']]),
                                     "issue": "; ".join(EXCLUDE_CODES[k] for k in sorted(kinds)),
                                     "action": "excluded"})
                    continue
                tops = {topic_of(c) for _, c, _ in lv if c not in EXCLUDE_CODES}
                if (len(tops) == 1 and not xs) or not L["romans"]:
                    t = tops.pop() if tops else None
                    units.append(([L["label"]], t, {t: L["marks"]}, []))
                    continue
                # mixed topics: try splitting into groups of consecutive same-topic romans
                groups = []
                for lab, code, mk in lv:
                    t = topic_of(code)
                    if groups and groups[-1][1] == t:
                        groups[-1][0].append(lab)
                        groups[-1][2] += mk
                    else:
                        groups.append([[lab], t, mk])
                ok, why = True, ""
                if L["ms_letter_level"]:
                    ok, why = False, "MS rows are at lettered-part level"
                for g in groups:
                    if not ok:
                        break
                    r = resolve(Q, g[0])
                    if not r["ok"]:
                        ok, why = False, r["why"]
                        break
                    sib = [c for c in r["ctx_parts"] if letter_of(c) == L["letter"] and c not in g[0]
                           and not c.endswith("#intro")]
                    if sib:
                        ok, why = False, f"{g[0][0]} depends on sibling {sib}"
                        break
                    qp, ms = marks(Q, g[0])
                    if ms is None or qp != ms:
                        ok, why = False, f"marks for {g[0]} not attributable ({qp} vs {ms})"
                        break
                    h = sum(cx.height(qd, unit_region(Q, c)) for c in r["ctx_parts"]) + cx.height(qd, L["intro"])
                    if h > MAX_CTX_H:
                        ok, why = False, f"context for {g[0]} exceeds one page"
                        break
                if ok:
                    for g in groups:
                        if g[1] is None:
                            kinds = {T[(pid, Q["n"], lab)] for lab in g[0]}
                            key = "pre_release" if kinds == {"PR"} else "out_of_syllabus"
                            log[key].append({"ref": ref_units(p['ref'], Q['n'], g[0]),
                                             "issue": "; ".join(EXCLUDE_CODES[k] for k in sorted(kinds)),
                                             "action": "excluded (rest of the lettered part kept)"})
                            continue
                        units.append((g[0], g[1], {g[1]: g[2]}, ["split"]))
                    log["split"].append({"ref": ref_units(p['ref'], Q['n'], [L['label']]),
                                         "groups": [[ref_units(p['ref'], Q['n'], g[0]), g[1]] for g in groups]})
                elif xs:
                    log["out_of_syllabus"].append({"ref": ref_units(p['ref'], Q['n'], [L['label']]),
                                                   "issue": f"contains sub-part(s) {xs} that are out of syllabus or "
                                                            f"need pre-release material and cannot be separated "
                                                            f"({why})", "action": "excluded"})
                    continue
                else:
                    t, by, tie = majority(lv)
                    flags = ["tie"] if tie else []
                    units.append(([L["label"]], t, by, flags))
                    if tie:
                        log["auto"].append({"ref": ref_units(p['ref'], Q['n'], [L['label']]),
                                            "issue": f"topic marks tie {by}",
                                            "action": f"filed under topic {t} (topic of first sub-part)"})
                    log["kept_whole"].append({"ref": ref_units(p['ref'], Q['n'], [L['label']]), "why": why, "by": by})
            # one item per question per unit (audit A-029, decision D3): all parts of a
            # question filed in the same unit form one item with one stem; if that item
            # fails a check, fall back to merging only dependent adjacent parts
            merged = []
            for t in dict.fromkeys(u[1] for u in units):
                grp = [u for u in units if u[1] == t]
                if len(grp) > 1:
                    us = [x for g in grp for x in g[0]]
                    r = resolve(Q, us)
                    qp, ms = marks(Q, us)
                    h = sum(cx.height(qd, unit_region(Q, c)) for c in r["ctx_parts"]) if r["ok"] else 0
                    if r["ok"] and ms is not None and qp == ms and h <= MAX_CTX_H:
                        by = {}
                        for g in grp:
                            for k, v in g[2].items():
                                by[k] = by.get(k, 0) + v
                        merged.append((us, t, by, [f for g in grp for f in g[3]] + ["merged"]))
                        continue
                    log["auto"].append({"ref": ref_units(p["ref"], Q["n"], us), "issue": "same-unit parts could "
                                        "not be merged into one item", "action": "kept as separate items"})
                for u in grp:
                    if merged and merged[-1][1] == u[1]:
                        r = resolve(Q, u[0])
                        prev = merged[-1][0]
                        dep = r["ok"] and any(c.replace("#intro", "") in prev or
                                              any(c.replace("#intro", "").startswith(pv) for pv in prev)
                                              for c in r["ctx_parts"])
                        if dep:
                            qp_, ms_ = marks(Q, prev + u[0])
                            dep = ms_ is not None and qp_ == ms_      # else keep apart: one bad part must not
                        if dep:                                       # take a good one with it
                            by = dict(merged[-1][2])
                            for k, v in u[2].items():
                                by[k] = by.get(k, 0) + v
                            merged[-1] = (prev + u[0], u[1], by, merged[-1][3] + u[3] + ["merged"])
                            continue
                    merged.append(u)
            merged.sort(key=lambda m: _order_key(Q, m[0][0]))
            # an item whose context would exceed one page forms one unsplittable block with
            # the parts it depends on: filed under the unit with most marks, tagged "also"
            changed = True
            while changed:
                changed = False
                for idx, (us, t, by, flags) in enumerate(merged):
                    if t is None:
                        continue
                    r = resolve(Q, us)
                    if not r["ok"]:
                        continue
                    h = sum(cx.height(qd, unit_region(Q, c)) for c in r["ctx_parts"])
                    if h <= MAX_CTX_H:
                        continue
                    need = [c.replace("#intro", "") for c in r["ctx_parts"]]
                    partners = [j for j, m in enumerate(merged) if j != idx and m[1] is not None and any(
                        n == u2 or n.startswith(u2) or u2.startswith(n) for n in need for u2 in m[0])]
                    if not partners:
                        continue
                    group = sorted([idx] + partners)
                    new_us = sorted({u for j in group for u in merged[j][0]}, key=lambda u: _order_key(Q, u))
                    qp_, ms_ = marks(Q, new_us)
                    if ms_ is None or qp_ != ms_:
                        continue
                    new_by = {}
                    for j in group:
                        for k, v in merged[j][2].items():
                            new_by[k] = new_by.get(k, 0) + v
                    best = max(new_by.values())
                    tops = [k for k, v in new_by.items() if v == best]
                    first_t = next(merged[j][1] for j in group if merged[j][1] in tops)
                    new_t = tops[0] if len(tops) == 1 else first_t
                    new_flags = sorted({f for j in group for f in merged[j][3]} | {"block"})
                    log["kept_whole"].append({"ref": ref_units(p["ref"], Q["n"], new_us),
                                              "why": f"context of {ref_units(p['ref'], Q['n'], us)} would exceed one "
                                                     f"page ({h:.0f} pt): kept with the parts it depends on",
                                              "by": new_by})
                    if len(tops) > 1:
                        log["auto"].append({"ref": ref_units(p["ref"], Q["n"], new_us),
                                            "issue": f"topic marks tie {new_by}",
                                            "action": f"filed under topic {new_t} (topic of first part)"})
                    merged = [m for j, m in enumerate(merged) if j not in group]
                    merged.append((new_us, new_t, new_by, new_flags))
                    merged.sort(key=lambda m: _order_key(Q, m[0][0]))
                    changed = True
                    break
            for us, t, by, flags in merged:
                ref = ref_units(p["ref"], Q["n"], us)
                if t is None:
                    continue
                r = resolve(Q, us)
                if not r["ok"]:
                    log["excluded"].append({"ref": ref, "issue": r["why"], "action": "excluded"})
                    continue
                qp, ms = marks(Q, us)
                if ms is None or qp != ms:
                    log["excluded"].append({"ref": ref, "issue": f"item [marks] {qp} != MS marks {ms}",
                                            "action": "excluded"})
                    continue
                h = sum(cx.height(qd, unit_region(Q, c)) for c in r["ctx_parts"])
                if h > MAX_CTX_H:
                    log["excluded"].append({"ref": ref, "issue": f"context exceeds one page ({h:.0f} pt)",
                                            "action": "excluded"})
                    continue
                for n in r["notes"]:
                    log["auto"].append({"ref": ref, "issue": n.split(":")[0], "action": n})
                for c in r["ctx_parts"]:
                    log["context"].append({"ref": ref, "part": c, "why": r["why_ctx"].get(c, "")})
                also = {k: v for k, v in by.items() if k != t and v}
                # the item's learning outcomes, from its own leaves
                los = []
                for u in us:
                    Lt = _L(Q, u)
                    for lab in ([R["label"] for R in Lt["romans"]] if (u == Lt["label"] and Lt["romans"]) else [u]):
                        c = T[(pid, Q["n"], lab)]
                        if c in LOS and c not in los:
                            los.append(c)
                # the insert (λ-cs/CLAUDE-cs.md, Sources): a note when the paper's insert
                # matches the Appendix copy in text, else that insert's pages inline
                text = " ".join([Q["stem_text"]] + [find_letter(Q, letter_of(i))["intro_text"] for i in r["intros"]]
                                + [items_text(Q, u) for u in us] + [items_text(Q, c) for c in r["ctx_parts"]])
                ins_mode, ins_pages, ins_why = ins.for_item(p, r["insert"], r["appendix"], text)
                if ins_mode:
                    log["insert"].append({"ref": ref, "mode": ins_mode, "why": ins_why,
                                          "pages": ins_pages})
                if book_of(t) != p["paper"]:
                    log["cross_filed"].append({"ref": ref, "unit": t,
                                               "action": f"Paper {p['paper']} part filed in the Paper {book_of(t)} "
                                                         f"book (unit {t})"})
                items.append({"ref": ref, "paper": pid, "paper_ref": p["ref"], "code": p["code"], "year": p["year"],
                              "series": p["series"], "variant": p["variant"], "paper_no": p["paper"],
                              "q": Q["n"], "units": us, "book": book_of(t),
                              "topic": t, "marks": qp, "by_topic": {str(k): v for k, v in by.items()},
                              "also": {str(k): v for k, v in also.items()}, "intros": r["intros"],
                              "ctx_parts": r["ctx_parts"], "ctx_blocks": [], "flags": flags,
                              "deps": r["deps"], "los": los, "sections": sorted({section_of(c) for c in los},
                                                                                key=lambda x: float(x.split(".")[1])),
                              "insert": ins_mode, "insert_pages": ins_pages,
                              "sort": [p["year"], SERIES_ORDER[p["series"]], int(p["code"]), -p["variant"], -Q["n"],
                                       -_order_key(Q, us[0])]})
    return items, topics, log


def items_text(Q, lab):
    from items import unit_text
    return unit_text(Q, lab) or ""


def coverage(P, items, T, log):
    """Every lowest-level part of every included question appears in exactly one item."""
    seen = defaultdict(list)
    for it in items:
        Q = next(q for q in P[it["paper"]]["questions"] if q["n"] == it["q"])
        for u in it["units"]:
            L = _L(Q, u)
            labs = [R["label"] for R in L["romans"]] if (u == L["label"] and L["romans"]) else [u]
            for lab in labs:
                seen[(it["paper"], it["q"], lab)].append(it["ref"])
    allv = set()
    for pid, p in P.items():
        for Q in p["questions"]:
            for L in Q["letters"]:
                for lab in ([R["label"] for R in L["romans"]] if L["romans"] else [L["label"]]):
                    allv.add((pid, Q["n"], lab))
    gaps = sorted(allv - set(seen))
    dupes = sorted(k for k, v in seen.items() if len(v) > 1)
    return gaps, dupes


def main():
    phase = sys.argv[1]
    items, topics, log = assemble(phase)
    P = jload(work(f"parts_{phase}.json"))
    gaps, dupes = coverage(P, items, None, log)
    log["coverage_gaps"] = [list(g) for g in gaps]
    log["coverage_dupes"] = [list(d) for d in dupes]
    for k in ("excluded", "out_of_syllabus", "pre_release", "split", "kept_whole", "auto", "context", "insert",
              "cross_filed"):
        log.setdefault(k, [])
    jdump(items, work(f"items_{phase}.json"), indent=0)
    jdump(topics, work(f"topics_{phase}.json"), indent=0)
    jdump(log, work(f"log_{phase}.json"))
    per = defaultdict(int)
    for it in items:
        per[it["topic"]] += 1
    print(f"{phase}: items {len(items)}, leaves tagged {len(topics)}, excluded {len(log['excluded'])}, "
          f"out-of-syllabus {len(log['out_of_syllabus'])}, pre-release {len(log['pre_release'])}, "
          f"split {len(log['split'])}, kept whole (multi-unit) {len(log['kept_whole'])}, "
          f"ties {sum(1 for a in log['auto'] if 'tie' in a['issue'])}, cross-filed {len(log['cross_filed'])}, "
          f"insert notes {sum(1 for i in log['insert'] if i['mode'] == 'note')}, "
          f"insert inline {sum(1 for i in log['insert'] if i['mode'] == 'inline')}, "
          f"coverage gaps {len(gaps)} (excluded parts account for these), dupes {len(dupes)}")
    print("items/unit:", dict(sorted(per.items())))


if __name__ == "__main__":
    main()
