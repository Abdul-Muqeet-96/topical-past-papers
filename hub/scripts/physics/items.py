"""Context resolution and self-containment checks for candidate items.

An item is a set of 'units' of one question: a lettered part "(c)" (whole) or
roman sub-parts "(c)(ii)". resolve() returns the context blocks needed so the
item is solvable alone, or a failure reason.
"""
import re
from extract import refs_in, ELEMENT_LIKE

MAX_CONTEXT_H = 700   # ~ one page of context


def letter_of(lab):
    m = re.match(r"\(([a-z])\)", lab)
    return m.group(1) if m else None


def find_letter(Q, letter):
    for L in Q["letters"]:
        if L["letter"] == letter:
            return L
    return None


def unit_region(Q, lab):
    """Question-crop region for a part label: '(c)' -> full lettered part,
    '(c)(ii)' -> that sub-part only, '(c)#intro' -> the lettered intro only."""
    if lab.endswith("#intro"):
        L = find_letter(Q, letter_of(lab))
        return L["intro"] if L else None
    L = find_letter(Q, letter_of(lab)) if letter_of(lab) else (Q["letters"][0] if Q["letters"] else None)
    if L is None:
        return None
    if lab == L["label"] or "(" not in lab[3:]:
        return L["full"]
    for R in L["romans"]:
        if R["label"] == lab:
            return R["region"]
    return None


def unit_text(Q, lab):
    if lab.endswith("#intro"):
        L = find_letter(Q, letter_of(lab))
        return L["intro_text"] if L else None
    L = find_letter(Q, letter_of(lab)) if letter_of(lab) else (Q["letters"][0] if Q["letters"] else None)
    if L is None:
        return None
    if lab == L["label"]:
        return L["full_text"]
    for R in L["romans"]:
        if R["label"] == lab:
            return R["text"]
    return None


def leaves(Q, lab):
    """Lowest-level labels covered by unit label."""
    L = find_letter(Q, letter_of(lab)) if letter_of(lab) else Q["letters"][0]
    if lab == L["label"] and L["romans"]:
        return [R["label"] for R in L["romans"]]
    return [lab]


def all_leaves(Q):
    out = []
    for L in Q["letters"]:
        out += [R["label"] for R in L["romans"]] if L["romans"] else [L["label"]]
    return out


def covers(units, lab):
    """Is part label lab inside the item's units?"""
    for u in units:
        if lab == u or lab.startswith(u) or u.startswith(lab) and False:
            return True
    return False


def _site_covered(site, units, ctx_parts, intros):
    if site in ("stem", "Q"):
        return True
    if site in intros or site + "#intro" in ctx_parts:
        return True
    for u in list(units) + list(ctx_parts):
        if site == u or site.startswith(u):
            return True
    return False


def resolve(Q, units):
    """Return dict(ok, why, intros, ctx_parts, ctx_blocks, height_est, notes)."""
    units = list(units)
    intros = []
    for u in units:
        L = find_letter(Q, letter_of(u))
        if L and u != L["label"] and L["intro"] and L["label"] not in intros:
            intros.append(L["label"])
    ctx_parts, ctx_blocks, notes, deps = [], [], [], []
    texts = [(Q["stem_text"], None, None)] + [(find_letter(Q, letter_of(i))["intro_text"], letter_of(i), i)
                                               for i in intros] + \
            [(unit_text(Q, u) or "", letter_of(u), u) for u in units]
    # Data Booklet items are kept with a note (audit A-017, decision D4)
    data_booklet = False      # Physics: no Data Booklet note (spec: no chemistry-specific rules)
    todo = list(texts)
    seen = set()
    allleaves = all_leaves(Q)
    while todo:
        t, tl, tlab = todo.pop(0)
        if (t, tl) in seen:
            continue
        seen.add((t, tl))
        r = refs_in(t)
        # "(*)(i)" = a sibling roman of the text's own lettered part (audit A-010/A-018)
        r["parts"] = [(f"({tl})" if tl else "") + p[3:] if p.startswith("(*)") else p for p in r["parts"]]
        # Tables / Figs
        for k in r["tabs"]:
            if k not in Q["captions"]:
                # reference to a table/fig not in this question (e.g. data booklet) -> unresolved
                return _fail(f"{k} referenced but not found in this question")
            site = Q["cap_site"][k]
            if _site_covered(site, units, ctx_parts, intros) or k in ctx_blocks:
                continue
            if Q["blocks"].get(k):
                ctx_blocks.append(k)
            else:
                # no clean block: include the defining part as context
                if site not in ctx_parts:
                    ctx_parts.append(site)
                    todo.append((unit_text(Q, site) or "", letter_of(site), site.replace("#intro", "")))
                    notes.append(f"{k}: block not isolable, defining part {site} used as context")
        # part references
        for pr in r["parts"]:
            if letter_of(pr) is None or find_letter(Q, letter_of(pr)) is None:
                continue
            if any(pr == u or pr.startswith(u) for u in units):
                continue
            if pr in intros or any(letter_of(u) == letter_of(pr) and pr == f"({letter_of(u)})" for u in units):
                continue   # "the information in (c)" from inside (c): the intro, already included
            if any(pr == c or pr.startswith(c) for c in ctx_parts if not c.endswith("#intro")):
                continue
            if pr not in allleaves and not find_letter(Q, letter_of(pr)):
                continue
            # reference to a later part (e.g. "in (c) you will...") is not a dependency
            if _after(Q, pr, units, tlab):
                continue
            ctx_parts.append(pr)
            if _uses_answer(t, pr):
                deps.append(pr)
            todo.append((unit_text(Q, pr) or "", letter_of(pr), pr))
        # "your answer" with no explicit reference -> previous leaf
        if r["your"] and not r["parts"] and tlab:
            prev = _prev_leaf(Q, tlab)       # the leaf before the text that says "your answer"
            if prev and not any(prev == c or prev.startswith(c) for c in ctx_parts) \
                    and not any(prev.startswith(u) for u in units):
                ctx_parts.append(prev)
                deps.append(prev)
                todo.append((unit_text(Q, prev) or "", letter_of(prev), prev))
                notes.append(f"'your answer' -> previous part {prev}")
        # labels / numbered references defined elsewhere
        labs = [x for x in r["labels"] if x not in ELEMENT_LIKE or x in Q.get("labels_defined", [])]
        for key in ["L:" + x for x in labs] + ["N:" + x for x in r["nrefs"]]:
            site = Q["first_def"].get(key)
            if site is None or _site_covered(site, units, ctx_parts, intros):
                continue
            if _after(Q, site, units, tlab):
                continue
            # a label defined in a lettered intro: include that intro only
            L = find_letter(Q, letter_of(site)) if letter_of(site) else None
            if L is not None and site == L["label"] and L["romans"]:
                site = site + "#intro"
            ctx_parts.append(site)
            todo.append((unit_text(Q, site) or "", letter_of(site), site.replace("#intro", "")))
    # a sub-part shown as context comes with its lettered part's introduction,
    # which often holds what the reference points to (e.g. "the reaction described in (a)(i)")
    for c in list(ctx_parts):
        L = find_letter(Q, letter_of(c)) if letter_of(c) else None
        if L and c != L["label"] and not c.endswith("#intro") and L["intro"] and L["label"] not in intros \
                and L["label"] + "#intro" not in ctx_parts and not any(u == L["label"] for u in units):
            ctx_parts.append(L["label"] + "#intro")
    ctx_parts = _order_labels(Q, ctx_parts)
    # parts whose ANSWER the item uses (explicit part reference / "your answer"): their MS rows are shown
    deps = [c for c in ctx_parts if any(c == d or d.startswith(c) for d in deps)]
    return {"ok": True, "why": "", "intros": intros, "ctx_parts": ctx_parts, "ctx_blocks": sorted(ctx_blocks),
            "notes": notes, "deps": deps, "data_booklet": data_booklet}


def _fail(why):
    return {"ok": False, "why": why, "intros": [], "ctx_parts": [], "ctx_blocks": [], "notes": [], "deps": [],
            "data_booklet": False}


def _order_key(Q, lab):
    lab = lab.replace("#intro", "")
    order = []
    for L in Q["letters"]:
        order.append(L["label"])
        order += [R["label"] for R in L["romans"]]
    return order.index(lab) if lab in order else 999


def _order_labels(Q, labs):
    labs = sorted(set(labs), key=lambda l: _order_key(Q, l))
    # drop sub-parts already covered by an included lettered part
    out = []
    for l in labs:
        base = l.replace("#intro", "")
        if any(o != l and not o.endswith("#intro") and base.startswith(o) for o in labs):
            continue
        out.append(l)
    return out


def _uses_answer(t, pr):
    """Does the text use the ANSWER of part pr (not just something described in it)?"""
    lab = re.escape(pr[3:] if pr[:3] == pr[3:6] else pr)
    for m in re.finditer(r"\d?" + re.escape(pr) + "|" + r"\(" + re.escape(pr.split(")(")[-1].strip("()")) + r"\)", t):
        w = t[max(0, m.start() - 90):m.end() + 40]
        if re.search(r"answer|calculat|determin|found|value|result|obtained|deduced|estimate|\buse\b|\busing\b", w, re.I):
            return True
    return False


def _after(Q, lab, units, at=None):
    """Is lab a later part than the text that mentions it? (A reference from the stem counts as
    forward.) Physics fix: measured from the referencing text, not from the item's first unit, so
    a merged item's later part may depend on a part between its units (e.g. "the oil in (b)")."""
    if at is None:
        return True
    return _order_key(Q, lab) > _order_key(Q, at)


def _prev_leaf(Q, lab):
    lv = all_leaves(Q)
    first = leaves(Q, lab)[0]
    i = lv.index(first) if first in lv else -1
    return lv[i - 1] if i > 0 else None


def marks(Q, units):
    """QP marks and MS marks of the item's units; None for MS if not attributable."""
    qp = ms = 0
    for u in units:
        L = find_letter(Q, letter_of(u)) if letter_of(u) else Q["letters"][0]
        if u == L["label"]:
            qp += L["marks"]
            ms += L["ms_marks"]
        else:
            R = next(R for R in L["romans"] if R["label"] == u)
            if L["ms_letter_level"]:
                return R["marks"], None
            qp += R["marks"]
            ms += R["ms_marks"]
    return qp, ms
