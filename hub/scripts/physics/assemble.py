"""Stage 5: tag leaves with topics (topics.json) and assemble items per CLAUDE.md.

Usage: python3 hub/scripts/assemble.py phase1|phase2|all
Reads work/parts_<phase>.json + work/tags_<phase>.txt.
Writes work/items_<phase>.json, work/topics_<phase>.json, work/log_<phase>.json.
"""
import json, os, re, sys
from collections import defaultdict, OrderedDict
sys.path.insert(0, os.path.dirname(__file__))
from items import resolve, marks, find_letter, letter_of, unit_region, _order_key
from tags import load as load_tags
from parse import load
from crops import bands
from layout import Flow

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TOPICS = OrderedDict([
    (1, "Physical quantities and units"), (2, "Kinematics"), (3, "Dynamics"),
    (4, "Forces, density and pressure"), (5, "Work, energy and power"), (6, "Deformation of solids"),
    (7, "Waves"), (8, "Superposition"), (9, "Electricity"), (10, "D.C. circuits"), (11, "Particle physics")])
# 2025-27 AS sections (Ω-physics/reference/physics-syllabus.pdf); learning outcomes in Ω-physics/build/work/syllabus_AS.txt
SECTIONS = {
    "1.1": "Physical quantities",
    "1.2": "SI units",
    "1.3": "Errors and uncertainties",
    "1.4": "Scalars and vectors",
    "2.1": "Equations of motion",
    "3.1": "Momentum and Newton's laws of motion",
    "3.2": "Non-uniform motion",
    "3.3": "Linear momentum and its conservation",
    "4.1": "Turning effects of forces",
    "4.2": "Equilibrium of forces",
    "4.3": "Density and pressure",
    "5.1": "Energy conservation",
    "5.2": "Gravitational potential energy and kinetic energy",
    "6.1": "Stress and strain",
    "6.2": "Elastic and plastic behaviour",
    "7.1": "Progressive waves",
    "7.2": "Transverse and longitudinal waves",
    "7.3": "Doppler effect for sound waves",
    "7.4": "Electromagnetic spectrum",
    "7.5": "Polarisation",
    "8.1": "Stationary waves",
    "8.2": "Diffraction",
    "8.3": "Interference",
    "8.4": "The diffraction grating",
    "9.1": "Electric current",
    "9.2": "Potential difference and power",
    "9.3": "Resistance and resistivity",
    "10.1": "Practical circuits",
    "10.2": "Kirchhoff's laws",
    "10.3": "Potential dividers",
    "11.1": "Atoms, nuclei and radiation",
    "11.2": "Fundamental particles",
}
LOS = {}
for _l in open(os.path.join(ROOT, "Ω-physics", "build", "work", "syllabus_AS.txt")):
    _m = re.match(r"^(\d+\.\d+\.\d+) (.*)", _l.strip())
    if _m:
        LOS[_m.group(1)] = _m.group(2)


def justification(code):
    """'3.1.4 Momentum and Newton's laws of motion: define and use force as rate of change of momentum'"""
    sec = ".".join(code.split(".")[:2])
    return f"{code} {SECTIONS.get(sec, '')}: {LOS.get(code, 'no clear syllabus match')}"


SERIES_ORDER = {"w": 3, "s": 2, "m": 1}
MAX_CTX_H = 700


def topic_of(code):
    return None if code == "X" else int(code.split(".")[0])


def ref_units(paper_ref, q, units):
    """Reference in the Physics-booklet style (audit A-027, decision D1):
    Q5/b, Q5/b(ii), Q3/b(ii,iii), Q3/a,b,c, Q6/a,b(i,ii,iii)."""
    groups = []          # [letter, [romans]] in paper order
    for u in units:
        lab = u.replace("#intro", "")
        m = re.match(r"\(([a-z])\)(?:\(([ivx]+)\))?$", lab)
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
            self.docs[f] = load(os.path.join(ROOT, "hub", "data", f))
        return self.docs[f]

    def height(self, doc, region):
        return Flow.bands_height(bands(doc, region), 1.0) if region else 0


def ctx_height(cx, qd, Q, ctx_parts, ctx_blocks, extra=()):
    """Height of the context as it is laid out: the union of the context regions (a figure
    inside a context part is not counted twice), cropped like the book."""
    regs = []
    for c in ctx_parts:
        regs += unit_region(Q, c) or []
    for b in ctx_blocks:
        regs += Q["blocks"][b] or []
    for e in extra:
        regs += e or []
    regs = sorted([list(r) for r in regs], key=lambda r: (r[0], r[1]))
    out = []
    for p, y0, y1 in regs:
        if out and out[-1][0] == p and y0 <= out[-1][2] + 0.5:
            out[-1][2] = max(out[-1][2], y1)
        else:
            out.append([p, y0, y1])
    return cx.height(qd, out)


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
    P = json.load(open(os.path.join(ROOT, "Ω-physics", "build", "work", f"parts_{phase}.json")))
    T = load_tags(phase)
    cx = Ctx()
    items, topics, log = [], [], defaultdict(list)
    for pid, p in sorted(P.items()):
        qd = cx.doc(p["qp"])
        for Q in p["questions"]:
            units = []   # (units list, topic, by-topic marks, flags)
            for L in Q["letters"]:
                lv = leaf_info(Q, L, T, pid)
                for lab, code, mk in lv:
                    topics.append({"ref": ref_units(p['ref'], Q['n'], [lab]), "paper": pid, "q": Q["n"], "part": lab,
                                   "topic": topic_of(code), "section": code,
                                   "justification": justification(code),
                                   "marks": mk})
                xs = [l for l, c, _ in lv if c == "X"]
                if xs and (len(xs) == len(lv) or not L["romans"]):
                    log["out_of_syllabus"].append({"ref": ref_units(p['ref'], Q['n'], [L['label']]),
                                                   "issue": "no clear match in current learning outcomes",
                                                   "action": "excluded"})
                    continue
                tops = {topic_of(c) for _, c, _ in lv if c != "X"}
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
                    h = ctx_height(cx, qd, Q, r["ctx_parts"], r["ctx_blocks"], extra=[Q["stem"], L["intro"]])
                    if h > MAX_CTX_H:
                        ok, why = False, f"context for {g[0]} exceeds one page"
                        break
                if ok:
                    for g in groups:
                        if g[1] is None:
                            log["out_of_syllabus"].append({"ref": ref_units(p['ref'], Q['n'], g[0]),
                                                           "issue": "no clear match in current learning outcomes",
                                                           "action": "excluded (rest of the lettered part kept)"})
                            continue
                        units.append((g[0], g[1], {g[1]: g[2]}, ["split"]))
                    log["split"].append({"ref": ref_units(p['ref'], Q['n'], [L['label']]),
                                         "groups": [[ref_units(p['ref'], Q['n'], g[0]), g[1]] for g in groups]})
                elif xs:
                    log["out_of_syllabus"].append({"ref": ref_units(p['ref'], Q['n'], [L['label']]),
                                                   "issue": f"contains out-of-syllabus sub-part(s) {xs} that cannot "
                                                            f"be separated ({why})", "action": "excluded"})
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
                    h = ctx_height(cx, qd, Q, r["ctx_parts"], r["ctx_blocks"]) if r["ok"] else 0
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
                            by = dict(merged[-1][2])
                            for k, v in u[2].items():
                                by[k] = by.get(k, 0) + v
                            merged[-1] = (prev + u[0], u[1], by, merged[-1][3] + u[3] + ["merged"])
                            continue
                    merged.append(u)
            merged.sort(key=lambda m: _order_key(Q, m[0][0]))
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
                h = ctx_height(cx, qd, Q, r["ctx_parts"], r["ctx_blocks"])
                if h > MAX_CTX_H:
                    log["excluded"].append({"ref": ref, "issue": f"context exceeds one page ({h:.0f} pt)",
                                            "action": "excluded"})
                    continue
                for n in r["notes"]:
                    log["auto"].append({"ref": ref, "issue": n.split(":")[0], "action": n})
                also = {k: v for k, v in by.items() if k != t and v}
                items.append({"ref": ref, "paper": pid, "paper_ref": p["ref"], "year": p["year"],
                              "series": p["series"], "variant": p["variant"], "q": Q["n"], "units": us,
                              "topic": t, "marks": qp, "by_topic": {str(k): v for k, v in by.items()},
                              "also": {str(k): v for k, v in also.items()}, "intros": r["intros"],
                              "ctx_parts": r["ctx_parts"], "ctx_blocks": r["ctx_blocks"], "flags": flags,
                              "deps": r["deps"], "data_booklet": r["data_booklet"],
                              "sort": [p["year"], SERIES_ORDER[p["series"]], -p["variant"], -Q["n"],
                                       -_order_key(Q, us[0])]})
    return items, topics, log


def coverage(P, items, T, log):
    """Every lowest-level part of every included question appears in exactly one item."""
    seen = defaultdict(list)
    for it in items:
        Q = next(q for q in P[it["paper"]]["questions"] if q["n"] == it["q"])
        for u in it["units"]:
            L = find_letter(Q, letter_of(u)) if letter_of(u) else Q["letters"][0]
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
    P = json.load(open(os.path.join(ROOT, "Ω-physics", "build", "work", f"parts_{phase}.json")))
    gaps, dupes = coverage(P, items, None, log)
    excl_refs = {e["ref"] for e in log["excluded"] + log["out_of_syllabus"]}
    log["coverage_gaps"] = [list(g) for g in gaps]
    log["coverage_dupes"] = [list(d) for d in dupes]
    json.dump(items, open(os.path.join(ROOT, "Ω-physics", "build", "work", f"items_{phase}.json"), "w"), indent=0, ensure_ascii=False)
    json.dump(topics, open(os.path.join(ROOT, "Ω-physics", "build", "work", f"topics_{phase}.json"), "w"), indent=0, ensure_ascii=False)
    json.dump(log, open(os.path.join(ROOT, "Ω-physics", "build", "work", f"log_{phase}.json"), "w"), indent=1, ensure_ascii=False)
    per = defaultdict(int)
    for it in items:
        per[it["topic"]] += 1
    print(f"{phase}: items {len(items)}, leaves tagged {len(topics)}, excluded {len(log['excluded'])}, "
          f"out-of-syllabus {len(log['out_of_syllabus'])}, split {len(log['split'])}, kept whole (multi-topic) "
          f"{len(log['kept_whole'])}, ties {sum(1 for a in log['auto'] if 'tie' in a['issue'])}, "
          f"coverage gaps {len(gaps)} (excluded parts account for these), dupes {len(dupes)}")
    print("items/unit:", dict(sorted(per.items())))


if __name__ == "__main__":
    main()
