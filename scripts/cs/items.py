"""Context resolution and self-containment checks for candidate items.

An item is a set of 'units' of one question: a lettered part "(c)" (whole) or
roman sub-parts "(c)(ii)". resolve() returns the context needed so the item is
solvable alone, or a failure reason.

Context sources (λ-cs/CLAUDE-cs.md):
- the stem and the lettered introduction (always shown);
- an earlier part named in the text ("part (a)", "1(b)(i)", "(ii)");
- "use your answer" with no part named -> the previous part;
- the identifier rule: a procedure, function, array, record type, variable,
  file or table name first used in an earlier part -> that part (question
  crop only);
- a single-letter label (gate X, device A) first used in an earlier part;
- a scenario noun used with "the/this" ("the program", "this algorithm") that
  the item itself and the stem never introduce -> the earlier part that does.
"""
import re
from extract import refs_in, anaphora, GENERIC, NOUNS

MAX_CONTEXT_H = 744   # one page of the book (page height less margins)


def letter_of(lab):
    m = re.match(r"\(([a-z])\)", lab)
    return m.group(1) if m else None


def find_letter(Q, letter):
    for L in Q["letters"]:
        if L["letter"] == letter:
            return L
    return None


def _L(Q, lab):
    """The lettered part a label belongs to. A question whose sub-parts are
    romans directly under the question number ("(i)", "(ii)") has one unnamed
    lettered part; "(i)" is then a roman, not the letter i."""
    L = find_letter(Q, letter_of(lab)) if letter_of(lab) else None
    if L is None and Q["letters"] and Q["letters"][0]["letter"] is None:
        return Q["letters"][0]
    return L


def unit_region(Q, lab):
    """Question-crop region for a part label: '(c)' -> full lettered part,
    '(c)(ii)' -> that sub-part only, '(c)#intro' -> the lettered intro only."""
    if lab.endswith("#intro"):
        L = _L(Q, lab[:-6])
        return L["intro"] if L else None
    L = _L(Q, lab)
    if L is None:
        return None
    if lab == L["label"]:
        return L["full"]
    for R in L["romans"]:
        if R["label"] == lab:
            return R["region"]
    return None


def unit_text(Q, lab):
    if lab.endswith("#intro"):
        L = _L(Q, lab[:-6])
        return L["intro_text"] if L else None
    L = _L(Q, lab)
    if L is None:
        return None
    if lab == L["label"]:
        return L["full_text"]
    for R in L["romans"]:
        if R["label"] == lab:
            return R["text"]
    return None


def unit_ids(Q, lab):
    if lab.endswith("#intro"):
        L = _L(Q, lab[:-6])
        return L["intro_ids"] if L else []
    L = _L(Q, lab)
    if L is None:
        return []
    if lab == L["label"]:
        return L["full_ids"]
    for R in L["romans"]:
        if R["label"] == lab:
            return R["ids"]
    return []


def leaves(Q, lab):
    """Lowest-level labels covered by unit label."""
    L = _L(Q, lab)
    if lab == L["label"] and L["romans"]:
        return [R["label"] for R in L["romans"]]
    return [lab]


def all_leaves(Q):
    out = []
    for L in Q["letters"]:
        out += [R["label"] for R in L["romans"]] if L["romans"] else [L["label"]]
    return out


def _site_covered(site, units, ctx_parts, intros):
    if site in ("stem", "Q"):
        return True
    if site in intros or site + "#intro" in ctx_parts:
        return True
    for u in list(units) + [c for c in ctx_parts if not c.endswith("#intro")]:
        if site == u or site.startswith(u):
            return True
    return False


def resolve(Q, units):
    """Return dict(ok, why, intros, ctx_parts, ctx_blocks, notes, deps, insert, why_ctx)."""
    units = list(units)
    intros = []
    for u in units:
        L = find_letter(Q, letter_of(u))
        if L and u != L["label"] and L["intro"] and L["label"] not in intros:
            intros.append(L["label"])
    ctx_parts, notes, deps, why_ctx = [], [], [], {}
    texts = [(Q["stem_text"], None, Q.get("stem_ids", []), "stem")]
    for i in intros:
        L = find_letter(Q, letter_of(i))
        texts.append((L["intro_text"], letter_of(i), L["intro_ids"], i + "#intro"))
    for u in units:
        texts.append((unit_text(Q, u) or "", letter_of(u), unit_ids(Q, u), u))
    uses_insert = any(refs_in(t)["insert"] for t, _, _, _ in texts)
    uses_appendix = any(refs_in(t)["appendix"] for t, _, _, _ in texts)
    todo = list(texts)
    seen = set()
    allleaves = all_leaves(Q)

    def add(site, why, dep=False):
        """Add a part (or lettered intro) as context and queue its own text."""
        L = find_letter(Q, letter_of(site)) if letter_of(site) else None
        if L is not None and site == L["label"] and L["romans"] and not dep and not why.startswith("part reference"):
            site = site + "#intro"          # something defined in a lettered intro: that intro only
        if site in ctx_parts:
            return
        ctx_parts.append(site)
        why_ctx.setdefault(site, why)
        if dep:
            deps.append(site)
        todo.append((unit_text(Q, site) or "", letter_of(site), unit_ids(Q, site), site))

    while todo:
        t, tl, ids, where = todo.pop(0)
        if (where, t) in seen:
            continue
        seen.add((where, t))
        r = refs_in(t, Q["n"])
        if r["xq"] and where in units:
            return _fail(f"refers to another question ({', '.join(r['xq'])})")
        # "(*)(i)" = a sibling roman of the text's own lettered part
        r["parts"] = [(f"({tl})" if tl else "") + p[3:] if p.startswith("(*)") else p for p in r["parts"]]
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
            if pr not in allleaves and find_letter(Q, letter_of(pr))["label"] != pr:
                continue          # e.g. "(b)(iv)" that does not exist
            if _not_before(Q, pr, where, units):
                # a reference to a later part is not a dependency, unless the text sends the
                # reader there for material it needs ("the pseudocode which follows in part (b)")
                lt = re.escape(letter_of(pr))
                if re.search(rf"(which follows|that follows|follows|shown|given|described|below)\b[^.]{{0,40}}\bpart \({lt}\)", t):
                    add(pr, "part reference (material printed in a later part)")
                continue
            add(pr, "part reference", dep=True)
        if r["your"] and not r["parts"] and where in units:
            prev = _prev_leaf(Q, units[0])
            if prev and not any(prev == c or prev.startswith(c) for c in ctx_parts) \
                    and not any(prev.startswith(u) for u in units):
                add(prev, "'your answer' -> previous part", dep=True)
                notes.append(f"'your answer' -> previous part {prev}")
        # identifiers and single-letter labels first used in an earlier part
        for key, why in [("I:" + x, "identifier " + x) for x in ids] + \
                        [("L:" + x, "label " + x) for x in r["labels"]]:
            site = Q["first_def"].get(key)
            if site is None or _site_covered(site, units, ctx_parts, intros):
                continue
            if _not_before(Q, site, where, units):
                continue
            # already shown by an earlier part of the item (e.g. the part it refers to)?
            name = key[2:]
            if key.startswith("I:") and any(
                    re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", unit_text(Q, c) or "")
                    and not _not_before(Q, c, where, units)
                    for c in list(units) + ctx_parts + [i + "#intro" for i in intros] if c != where):
                continue
            add(site, why)
        # scenario nouns the item never introduces ("the algorithm" printed in part (a))
        if where in units or where.endswith("#intro") and where[:-6] in intros:
            for noun, pos in anaphora(t):
                if noun in GENERIC:
                    continue
                site = Q["first_def"].get("N:" + noun)
                if site is None or _site_covered(site, units, ctx_parts, intros) or \
                        _not_before(Q, site, where, units):
                    continue
                # introduced by this text itself before the use ("a network ... the network")?
                if re.search(rf"\b(a|an|following|each|one|two|three|some|another)\s+"
                                                rf"(\w+\s+)?{re.escape(noun)}\b", t[:pos], re.I):
                    continue
                add(site, "'the " + noun + "'")
    # a sub-part shown as context comes with its lettered part's introduction
    for c in list(ctx_parts):
        L = find_letter(Q, letter_of(c)) if letter_of(c) else None
        if L and c != L["label"] and not c.endswith("#intro") and L["intro"] and L["label"] not in intros \
                and L["label"] + "#intro" not in ctx_parts and not any(u == L["label"] for u in units):
            ctx_parts.append(L["label"] + "#intro")
            why_ctx.setdefault(L["label"] + "#intro", "intro of " + c)
    ctx_parts = _order_labels(Q, ctx_parts)
    deps = [c for c in ctx_parts if any(c == d or d.startswith(c) for d in deps)]
    return {"ok": True, "why": "", "intros": intros, "ctx_parts": ctx_parts, "ctx_blocks": [],
            "notes": notes, "deps": deps, "insert": uses_insert, "appendix": uses_appendix,
            "why_ctx": {c: why_ctx.get(c, "") for c in ctx_parts}}


def _fail(why):
    return {"ok": False, "why": why, "intros": [], "ctx_parts": [], "ctx_blocks": [], "notes": [], "deps": [],
            "insert": False, "appendix": False, "why_ctx": {}}


def _order_key(Q, lab):
    lab = lab.replace("#intro", "")
    order = []
    for L in Q["letters"]:
        order.append(L["label"])
        order += [R["label"] for R in L["romans"]]
    return order.index(lab) if lab in order else 999


def _order_labels(Q, labs):
    labs = sorted(set(labs), key=lambda l: (_order_key(Q, l), not l.endswith("#intro")))
    out = []
    for l in labs:
        base = l.replace("#intro", "")
        if any(o != l and not o.endswith("#intro") and base.startswith(o) for o in labs):
            continue      # covered by an included lettered part
        out.append(l)
    return out


def _after(Q, lab, units):
    first = min(_order_key(Q, u) for u in units)
    return _order_key(Q, lab) > first


def _not_before(Q, site, where, units):
    """True when 'site' does not come before the text that mentions it (so it
    cannot be something that text depends on)."""
    if where == "stem":
        return True
    w = where if _order_key(Q, where) != 999 else units[0]
    return _order_key(Q, site) >= _order_key(Q, w)


def _prev_leaf(Q, lab):
    lv = all_leaves(Q)
    first = leaves(Q, lab)[0]
    i = lv.index(first) if first in lv else -1
    return lv[i - 1] if i > 0 else None


def marks(Q, units):
    """QP marks and MS marks of the item's units; None for MS if not attributable."""
    qp = ms = 0
    for u in units:
        L = _L(Q, u)
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
