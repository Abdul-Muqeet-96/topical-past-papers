"""Context resolution and self-containment checks for candidate items.

An item is a set of 'units' of one question: a lettered part "(c)" (whole) or
roman sub-parts "(c)(ii)". resolve() returns the context blocks needed so the
item is solvable alone, or a failure reason.
"""
import re
from extract import refs_in

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
    '(c)(ii)' -> that sub-part only."""
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
    if site in intros:
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
    ctx_parts, ctx_blocks, notes = [], [], []
    texts = [Q["stem_text"]] + [find_letter(Q, letter_of(i))["intro_text"] for i in intros] + \
            [unit_text(Q, u) or "" for u in units]
    todo = list(texts)
    seen = set()
    allleaves = all_leaves(Q)
    while todo:
        t = todo.pop(0)
        if t in seen:
            continue
        seen.add(t)
        r = refs_in(t)
        # Tables / Figs
        for k in r["tabs"]:
            if k not in Q["captions"]:
                # reference to a table/fig not in this question (e.g. data booklet) -> unresolved
                if not re.search(r"Data Booklet", t, re.I):
                    return _fail(f"{k} referenced but not found in this question")
                continue
            site = Q["cap_site"][k]
            if _site_covered(site, units, ctx_parts, intros) or k in ctx_blocks:
                continue
            if Q["blocks"].get(k):
                ctx_blocks.append(k)
            else:
                # no clean block: include the defining part as context
                if site not in ctx_parts:
                    ctx_parts.append(site)
                    todo.append(unit_text(Q, site) or "")
                    notes.append(f"{k}: block not isolable, defining part {site} used as context")
        # part references
        for pr in r["parts"]:
            if letter_of(pr) is None or find_letter(Q, letter_of(pr)) is None:
                continue
            if any(pr == u or pr.startswith(u) for u in units):
                continue
            if any(pr == c or pr.startswith(c) for c in ctx_parts):
                continue
            if pr not in allleaves and not find_letter(Q, letter_of(pr)):
                continue
            # reference to a later part (e.g. "in (c) you will...") is not a dependency
            if _after(Q, pr, units):
                continue
            ctx_parts.append(pr)
            todo.append(unit_text(Q, pr) or "")
        # "your answer" with no explicit reference -> previous leaf
        if r["your"] and not r["parts"]:
            first = units[0]
            prev = _prev_leaf(Q, first)
            if prev and not any(prev == c or prev.startswith(c) for c in ctx_parts) \
                    and not any(prev.startswith(u) for u in units):
                ctx_parts.append(prev)
                todo.append(unit_text(Q, prev) or "")
                notes.append(f"'your answer' -> previous part {prev}")
        # labels / numbered references defined elsewhere
        for key in ["L:" + x for x in r["labels"]] + ["N:" + x for x in r["nrefs"]]:
            site = Q["first_def"].get(key)
            if site is None or _site_covered(site, units, ctx_parts, intros):
                continue
            if _after(Q, site, units):
                continue
            # site may be a lettered intro: include intro only (as ctx part label)
            ctx_parts.append(site)
            todo.append(unit_text(Q, site) or "")
    ctx_parts = _order_labels(Q, ctx_parts)
    return {"ok": True, "why": "", "intros": intros, "ctx_parts": ctx_parts, "ctx_blocks": sorted(ctx_blocks),
            "notes": notes}


def _fail(why):
    return {"ok": False, "why": why, "intros": [], "ctx_parts": [], "ctx_blocks": [], "notes": []}


def _order_key(Q, lab):
    order = []
    for L in Q["letters"]:
        order.append(L["label"])
        order += [R["label"] for R in L["romans"]]
    return order.index(lab) if lab in order else 999


def _order_labels(Q, labs):
    labs = sorted(set(labs), key=lambda l: _order_key(Q, l))
    # drop sub-parts already covered by an included lettered part
    return [l for l in labs if not any(l != o and l.startswith(o) for o in labs)]


def _after(Q, lab, units):
    first = min(_order_key(Q, u) for u in units)
    return _order_key(Q, lab) > first


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
