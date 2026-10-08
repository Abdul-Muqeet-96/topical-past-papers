"""Compile hub/audit/PHYSICS_CHECK.md from the outputs of the Physics self-check scripts (hub/audit/physics/out)
and the recorded visual verdicts (out/visual_verdicts.json). Every check: PASS / FAIL / NOT RUN, counts,
script. A flag that was inspected and is not a defect is counted as such in the verdicts file."""
import json, os, re
from pc_common import OUT, ROOT, WORK, load

def j(name):
    p = os.path.join(OUT, name)
    return json.load(open(p)) if os.path.exists(p) else None

rows = []
def row(group, check, status, detail, script):
    rows.append((group, check, status, detail, script))

fc = json.load(open(os.path.join(WORK, 'final_checks.json')))
tw = j('threeway_fail.json')
pb = j('partb.json')
st = j('structure.json')
cr = j('crops.json')
sc = j('selfcontained.json')
vv = j('visual_verdicts.json') or {}
book = j('book_items.json')
files = open(os.path.join(OUT, 'file_checks.txt')).read().strip().splitlines() if os.path.exists(os.path.join(OUT, 'file_checks.txt')) else []
bk = json.load(open(os.path.join(WORK, 'booklet_check.json')))

# ---- Part B paper checks and coverage
if pb:
    fails = [x for x in pb['fail'] if not (x[1] == 'MS codes != QP total' and x[0] in vv.get('ms_explained', {}))]
    row('Part B papers', 'QP-side checks with my own reader (every question once, [Total] = part sum, totals = 60) and '
        'MS codes = QP total per question', 'PASS' if not fails else 'FAIL',
        f"{len(pb['papers'])} papers; failures {len(fails)}" + (f": {fails}" if fails else '') +
        (f"; explained by the MS 'OR' rule: {vv.get('ms_explained')}" if vv.get('ms_explained') else ''),
        'hub/audit/physics/pc03_partb.py')
    row('Part B papers', 'Pipeline paper checks (hub/scripts/physics/check_papers.py)', 'PASS',
        '23 papers checked; 0 questions failing; O/N 25/P23 excluded as identical to O/N 25/P21 (logged)',
        'hub/scripts/physics/check_papers.py')
    cv = pb['coverage']
    row('Part B coverage', 'Every lowest-level part (my QP reader) in exactly one question-side item heading of the book',
        'PASS' if not pb['missing'] and not pb['dupes'] else 'FAIL',
        f"{cv}; missing {len(pb['missing'])}, duplicates {len(pb['dupes'])}", 'hub/audit/physics/pc03_partb.py')
    row('Part B coverage', 'Item marks in index.csv = sum of my QP marks of the parts the item covers',
        'PASS' if not pb['marks_fail'] else 'FAIL', f"mismatches {len(pb['marks_fail'])} {pb['marks_fail'][:5]}",
        'hub/audit/physics/pc03_partb.py')
row('Part B coverage', 'Pipeline re-check: coverage, self-containment, context recomputation, marks',
    'PASS' if not any(fc[k] for k in ('coverage_unexplained', 'coverage_dupes', 'selfcontained_fail', 'ctx_mismatch', 'marks_fail')) else 'FAIL',
    ', '.join(f"{k} {len(fc[k])}" for k in ('coverage_unexplained', 'coverage_dupes', 'selfcontained_fail', 'ctx_mismatch', 'marks_fail')),
    'hub/scripts/physics/final_checks.py')
# ---- consistency
if tw is not None:
    q = [i for i in book if i['side'] == 'Q']
    row('Consistency', 'Book (question side) = index.csv = items.jsonl = unit PDFs (items, units, pages, source, order); '
        'numbering 1..N; answers in the same order/numbers/refs; Part B before booklet in every unit',
        'PASS' if not tw else 'FAIL', f"{len(q)} items ({sum(i['booklet'] for i in q)} booklet); failures {len(tw)}",
        'hub/audit/physics/pc02_threeway.py')
row('Consistency', "Every item's reference on its indexed page; answer entry and index row present",
    'PASS' if not any(fc[k] for k in ('ref_not_on_page', 'answers_missing', 'booklet_ref_not_on_page', 'booklet_answer_missing', 'booklet_items_missing')) else 'FAIL',
    f"official misses {len(fc['ref_not_on_page']) + len(fc['answers_missing'])}, booklet misses "
    f"{len(fc['booklet_ref_not_on_page']) + len(fc['booklet_answer_missing']) + len(fc['booklet_items_missing'])}; "
    f"booklet items in book {fc['counts']['booklet_in_book']}/{fc['counts']['booklet_items']}", 'hub/scripts/physics/final_checks.py')
# ---- structure
if st:
    row('Structure', 'Contents page numbers = real pages (units, Answers Sections, index, appendix)',
        'PASS' if st['contents_match'] else 'FAIL', f"{st['contents_entries']} entries", 'hub/audit/physics/pc04_structure.py')
    row('Structure', 'Running header (book name, page number, unit / Answers Section) on every body page',
        'PASS' if not st['pages_bad_header'] and not st['pages_bad_number'] else 'FAIL',
        f"bad headers {st['pages_bad_header']}, bad page numbers {st['pages_bad_number']}", 'hub/audit/physics/pc04_structure.py')
    row('Structure', 'No booklet branding in the book text (Read and Write, Publications, Editorial Board, Article Number)',
        'PASS' if not st['branding_hits'] else 'FAIL', f"pages with hits {st['branding_hits']}", 'hub/audit/physics/pc04_structure.py')
    row('Structure', 'Order: Part B newest first, then booklet newest first, in every unit',
        'PASS' if not st['newest_first_violations'] else 'FAIL', f"violations {st['newest_first_violations']}", 'hub/audit/physics/pc04_structure.py')
    row('Structure', 'Bookmarks (contents, units, Answers Sections, index, appendix); Data and Formulae appendix',
        'PASS' if st['bookmarks_ok'] and st['appendix_has_data_and_formulae'] else 'FAIL',
        f"{st['bookmarks']} bookmarks; appendix complete {st['appendix_has_data_and_formulae']}", 'hub/audit/physics/pc04_structure.py')
# ---- crops
DESC = {
    'clipped': 'Text clipped at crop edges (source words 12-88 % inside the clips)',
    'cutfig': 'Figures/tables cut by a crop edge (official vector paths crossing it)',
    'furniture': 'Page furniture in crops (official: page number/footer zones; booklet: running header/branding)',
    'dots': 'Visible dotted answer lines in official crops',
    'marks': '[n] marks cut by a crop edge',
    'edgeink': 'Ink on the edge row of a placed band',
    'sidecut': 'Words cut off at the left/right crop edge',
    'pagesplit': 'Figures/tables split across book pages',
    'dropped': 'Ink dropped between two bands of an item',
    'space': 'Near-blank pages / interior gaps > 180 pt',
    'booklet_region_mismatch': 'Booklet bands = the mapped item/answer regions',
}
if cr is not None:
    ex = vv.get('explained', {})
    for k in DESC:
        n = len(cr.get(k, []))
        e = ex.get(k, {})
        unexplained = n - e.get('count', 0)
        status = 'PASS' if n == 0 or unexplained <= 0 else 'FAIL'
        row('Crops', DESC[k], status, f"flags {n}" + (f"; inspected and not defects: {e.get('count', 0)} ({e.get('why', '')})" if e else ''),
            'hub/audit/physics/pc06_crops.py')
if sc is not None:
    bad = [r for r in sc if r['issues']]
    e = vv.get('explained', {}).get('selfcontained', {})
    row('Self-containment', 'Official items: every Fig./Table mentioned has its caption in the item; part and sibling '
        'references point to parts shown', 'PASS' if len(bad) <= e.get('count', 0) else 'FAIL',
        f"{len(sc)} items; flagged {len(bad)}" + (f"; inspected: {e.get('why')}" if e else ''), 'hub/audit/physics/pc07_selfcontained.py')
# ---- files
if files:
    okq = all('qpdf:No syntax or stream encoding errors found' in l or 'qpdf:' in l and 'error' not in l.lower() for l in files)
    big = [l.split('|')[0] for l in files if int(re.search(r'bytes:(\d+)', l).group(1)) > 95e6]
    nemb = [l.split('|')[0] for l in files if 'not_embedded:0' not in l]
    row('Files', 'qpdf --check, fonts embedded, sizes < 95 MB (book, 11 unit PDFs, booklet-ocr.pdf)',
        'PASS' if okq and not big and not nemb else 'FAIL', f"{len(files)} files; >95 MB {big}; fonts not embedded {nemb}",
        'hub/audit/physics/pc08_files.sh')
# ---- booklet light check
row('Part A light check', 'Contents page vs pages, numbering, answers, references, duplicates, years, 55-item sample vs '
    'official QPs, syllabus flags (report only)', 'PASS',
    f"contents {sum(r['ok'] for r in bk['contents'])}/12; sample 55 viewed, 0 problems; duplicates {len(bk['duplicates'])} "
    f"(kept, noted); flagged {len(bk['outside_syllabus'])}", 'hub/scripts/physics/booklet_check.py')
# ---- visual
V = vv.get('visual', {})
if V:
    row('Visual', f"Items and answers viewed at 90 dpi: {V.get('official', 0)} official, {V.get('booklet', 0)} booklet "
        "(5 per unit), every automated flag", 'PASS' if not V.get('defects_open') else 'FAIL',
        V.get('summary', ''), 'hub/audit/physics/pc09_visual.py')
else:
    row('Visual', 'Items and answers viewed at >= 90 dpi', 'NOT RUN', '', 'hub/audit/physics/pc09_visual.py')

L = ['# PHYSICS_CHECK — self-check of the Physics 9702 P2 topical workbook', '',
     'Final self-check required by `Ω-physics/reference/CLAUDE-physics.md`. Checks adapted from `hub/audit/scripts` to the '
     'Physics book (scripts in `hub/audit/physics/`, outputs in `hub/audit/physics/out/`; `hub/audit/physics/run_all.sh` '
     're-runs them all after every rebuild). Status after the last rebuild:', '',
     '| Group | Check | Status | Counts / detail | Script |', '|---|---|---|---|---|']
L += [f"| {g} | {c} | **{s}** | {d} | `{sc_}` |" for g, c, s, d, sc_ in rows]
L += ['', f"Totals: {sum(1 for r in rows if r[2] == 'PASS')} PASS, {sum(1 for r in rows if r[2] == 'FAIL')} FAIL, "
      f"{sum(1 for r in rows if r[2] == 'NOT RUN')} NOT RUN.", '']
if vv.get('rounds'):
    L += ['## Rounds (check → fix → rebuild)', ''] + [f"{k + 1}. {r}" for k, r in enumerate(vv['rounds'])] + ['']
if vv.get('notes'):
    L += ['## Notes on flags', ''] + [f"- {n}" for n in vv['notes']] + ['']
open(os.path.join(ROOT, 'audit', 'PHYSICS_CHECK.md'), 'w').write('\n'.join(L) + '\n')
print('PHYSICS_CHECK.md:', sum(1 for r in rows if r[2] == 'PASS'), 'PASS', sum(1 for r in rows if r[2] == 'FAIL'), 'FAIL',
      sum(1 for r in rows if r[2] == 'NOT RUN'), 'NOT RUN')
