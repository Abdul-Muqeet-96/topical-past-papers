"""Write audit/findings.csv from the audit evidence files (audit/out/*.json) plus the manually verified
observations recorded below. Item lists are computed from the evidence, not typed."""
import csv, json

bi = json.load(open('audit/out/book_items.json'))
PG = {(i['ref'], i['side']): i['page'] for i in bi}
def q(ref): return PG.get((ref, 'Q'))
def a(ref): return PG.get((ref, 'A'))
def fmt(refs, side='Q'):
    return '; '.join(f"{r} (p{PG.get((r, side))})" for r in refs)

dropped = json.load(open('audit/out/dropped_ink.json'))
A001 = sorted({x['ref'] for x in dropped if x['ref'].startswith('M/J 22/P21/Q3')})
A002 = sorted({x['ref'] for x in dropped
               if not x['ref'].startswith('M/J 22/P21/Q3') and not x['ref'].startswith('M/J 24/P22')})
furn = json.load(open('audit/out/furniture.json'))['furniture']
A005 = sorted({r['ref'] for r in furn if r['ref'].startswith('MAR 20')})
A006 = sorted({r['ref'] for r in furn if r['ref'].startswith('M/J 24/P22')})
dup = [d[0] for d in json.load(open('audit/out/context_blocks.json'))['dup']]
tags = json.load(open('audit/out/tag_compare.json'))
dis = [t for t in tags if t['status'] == 'DISAGREE']

F = []
def add(id_, sev, check, refs, what, evidence, method, fix, mode):
    F.append(dict(id=id_, severity=sev, check=check, items_and_pages=refs, finding=what,
                  evidence=evidence, method=method, proposed_fix=fix, fix_type=mode))

add('A-001', 'Critical', '6 Crop quality', fmt(A001),
    'Skeletal formulae altered: whitespace removal dropped source rows that contain the methyl/isopropyl branches of T (Fig. 3.1), Q and R (Fig. 3.3) and R (Fig. 3.4). The book shows unbranched or stub-branched molecules, which changes the chemistry (e.g. the stereoisomerism asked in Q3(a)). In Q3(d)(iii) Fig. 3.1 (wrong) and Fig. 3.2 (right) now disagree.',
    'Dropped source strips 9701_s22_qp_21 p7 y100.3-126.4, p9 y113.6-139.8, p9 y456.5-483.3 contain only graphic ink (no text); side-by-side render of book p688/p486 vs source p7/p9.',
    'a80b_dropped_ink.py (pixel scan of rows dropped between consecutive bands) + visual comparison',
    'Never drop source rows inside a figure: if a candidate gap row has any non-dotted ink within the band x-range, keep it (merge the two bands). Re-crop Figs. 3.1/3.3/3.4 of M/J 22/P21 as single bands and rebuild the 6 items.', 'automatic')
add('A-002', 'Major', '6 Crop quality', fmt(A002),
    'Figure lines broken by white stripes: bond lines (C-H, C=O, C-Br, C≡N), branch stubs and box edges are cut where the build removed rows it judged empty. Structures stay recognisable but bonds look dashed or detached (e.g. acetoin C=O in M/J 16/P23/Q4, structure G in M/J 22/P23/Q3, R in MAR 21/P22/Q3).',
    '53 dropped strips with graphic-only ink in 41 items (35 here, 6 in A-001); visually confirmed on M/J 22/P23/Q3(a)(i) p176 vs source p6, MAR 21/P22/Q3(b)(ii) p184, M/J 16/P23/Q4(a) p739.',
    'a80b_dropped_ink.py, a79_split_gaps.py (vertical lines crossing dropped strips), visual comparison',
    'Same rule as A-001 (keep rows with figure ink). Rebuild the listed items.', 'automatic')
add('A-003', 'Major', '6 Crop quality', f"M/J 23/P22/Q4(c)(iv)-(v) (p{q('M/J 23/P22/Q4(c)(iv)-(v)')})",
    'The "Context: Fig. 4.2" block shows only the bottom half of Fig. 4.2 (the H3C-CH2-O+-H / H3C-CH2-O-H structures, curly-arrow area and arrow are missing). Part (v) says "Use Fig. 4.1 and Fig. 4.2". A stray fragment of a "[2]" mark from (c)(iii) sits under the crop.',
    'Source 9701_s23_qp_22 p9 rendered vs book p425; a71_clipped.py flags "[2]" 31% inside; a72_cutfigs.py flags a path cut at y=195.6.',
    'a71_clipped.py, a72_cutfigs.py, a77_marks_clipped.py, visual',
    'Crop Fig. 4.2 from its top (the figure starts directly under the (c)(iii) text) to its caption; exclude the (c)(iii) mark line.', 'automatic')
add('A-004', 'Major', '6 Crop quality / 7 Self-containment', f"M/J 25/P23/Q5(b)(v) (p{q('M/J 25/P23/Q5(b)(v)')})",
    'Context "Fig. 5.3" (structure of Z, the item\'s subject) is cropped without its O-CH3 methyl line, so Z appears as an ester O with nothing attached. The IR spectrum\'s y-axis label "transmittance / %" is cut at the left crop edge. The Fig. 5.3 context is also placed before the stem.',
    'Source 9701_s25_qp_23 p10 vs book p1186; a71_clipped.py: "transmittance" hfrac 0.84, "500" 0.47.',
    'a71_clipped.py, visual',
    'Crop Fig. 5.3 including the methyl line; widen the band to x>=0 for figures whose labels sit in the left margin; place context in stem -> figure order.', 'automatic')
add('A-005', 'Major', '6 Crop quality', fmt(A005),
    'Page furniture inside crops for MAR 20/P22 (a scaled 0.9 page): "© UCLES 2020 9701/22/F/M/20 [Turn over" footer and the red PapaCambridge logo appear in the items.',
    'Footer words inside bands on 8 book pages; red-pixel logo scan hits pages 189, 248, 295, 376, 602, 817, 818, 1082; render of p376.',
    'a73_furniture.py (footer zone from actual footer text positions + red pixel scan)',
    'Detect the footer by its text (UCLES / paper code / Turn over) rather than a fixed y, and stop bands above it for scaled pages.', 'automatic')
add('A-006', 'Major', '6 Crop quality', fmt(A006),
    'Barcode strip, page number and black corner mark from the top of the next source page appear mid-item (page-break leftovers) in M/J 24/P22 items.',
    'Bands start above the source page-number line; a71_clipped.py: page numbers "3","5","7","8","11" 57% inside; render of p279 and p1146.',
    'a73_furniture.py, a71_clipped.py, visual',
    'Start continuation bands below the page-number/barcode zone (y > page-number bottom).', 'automatic')
add('A-007', 'Major', '1 Source / 2 Paper-level', 'M/J 15/P21 (all 4 questions, 27 parts; not in book)',
    'Whole paper wrongly excluded. report.md says "no questions found in QP text layer", but the QP has a normal text layer (it is an A3-scaled page, 842x1191 pt). Independently: questions 1-4 present once, part marks sum to [Total] 20/15/12/13, totals sum to 60, MS totals equal QP totals for every question.',
    'qp_parse.json / ms_parse.json for s15_21; parser normalises coordinates by page width.',
    'a20_qp_parse.py, a21_ms_parse.py',
    'Re-run extraction with coordinates normalised to page width; include the paper (Phase 2: syllabus filter still applies).', 'automatic')
add('A-008', 'Major', '2 Paper-level', 'M/J 16/P23 Q2, Q3; O/N 16/P21 Q2, Q3; O/N 16/P23 Q2, Q3 (48 parts; not in book)',
    'Six questions wrongly excluded as "MS marks != QP total". Independently the MS totals equal the QP totals (O/N 16/P21 Q2: part totals 3+1+1+1+2+3+2 = 13 = [Total: 13]). The build\'s old-layout MS reader double-counted point marks.',
    'Part-level comparison QP vs MS equal for O/N 16/P21+P23 Q2/Q3 at every leaf; M/J 16/P23 equal at letter level; render of 9701_w16_ms_21 p3.',
    'a21_ms_parse.py, a22_dbg.py, a23_msrow_img.py (visual)',
    'Re-run the MS check with part-total column handling and include the six questions.', 'automatic')
add('A-009', 'Major', '2 Paper-level / 5 Marks', 'O/N 23/P21 Q4; O/N 23/P23 Q4; M/J 26/P24 Q5(e),(f); M/J 18/P22 Q2(b),(c), Q3(b),(c); MAR 19/P22 Q3(a) (not in book)',
    'Exclusions caused by typos in the MS row labels ("4(a(i)", "5f)", "2c(i)", "3c(iii)", "3(e)" for 3(a)). The marks themselves match the QP. report.md gives incorrect causes ("MS marks 3", "MS marks 8", "MS marks 0"). Q2(b) and Q3(b) of M/J 18/P22 were excluded only as collateral of the neighbouring typo.',
    'MS rows rendered: 9701_s26_ms_24 p22-23 (5(e)=1, "5f)"=2), 9701_s18_ms_22 p6 ("2c(i)" 2 + 2c(ii) 2 = 4), p8 ("3c(iii)"), 9701_m19_ms_22 p8 ("3(e)" 3 marks for QP 3(a) [3]).',
    'a21_ms_parse.py (typo-tolerant label reading), a23_msrow_img.py, visual',
    'Decision needed: allow a typo-tolerant MS label match when it is unambiguous (single unmatched row whose marks equal the QP part) and record it in report.md; otherwise keep excluded but correct the stated reasons.', 'needs your choice')
add('A-010', 'Major', '7 Self-containment',
    f"M/J 16/P22/Q4(b)(ii) (p{q('M/J 16/P22/Q4(b)(ii)')}); M/J 16/P23/Q4(d)(ii)-(iv) (p{q('M/J 16/P23/Q4(d)(ii)-(iv)')}); O/N 19/P22/Q2(c)(ii) (p{q('O/N 19/P22/Q2(c)(ii)')}); O/N 22/P22/Q3(b) (p{q('O/N 22/P22/Q3(b)')})",
    'Items depend on an earlier part that is not shown: "one of your esters in (i)", "the product in (i)", "the amount of CO2 calculated in (i)", and compound "D2" (defined only in the Table 3.1 of part (a)). They cannot be answered alone.',
    'Item text has the reference but no line starting with that sub-part label / no Table 3.1.',
    'a92_roman_refs.py, a91_selfcontained.py, visual (sheet review)',
    'Add the referenced sub-part (question crop, answer lines removed) or Table 3.1 as context, with its MS row; or merge with the sibling item.', 'automatic')
add('A-011', 'Major', '11 Phase 2',
    f"O/N 19/P21/Q3(a)(iv) (p{q('O/N 19/P21/Q3(a)(iv)')}); O/N 19/P23/Q3(a)(iv) (p{q('O/N 19/P23/Q3(a)(iv)')}); M/J 17/P21/Q3(d)(ii) (p{q('M/J 17/P21/Q3(d)(ii)')}); M/J 15/P23/Q2(c) (p{q('M/J 15/P23/Q2(c)')}); M/J 19/P23/Q3(c) (p{q('M/J 19/P23/Q3(c)')}); MAR 17/P22/Q1(c)(ii) (p{q('MAR 17/P22/Q1(c)(ii)')})",
    'Phase-2 items kept that are not clearly covered by the 2025-27 outcomes: IR monitoring of atmospheric CO (22.1 only asks to analyse a spectrum); use of CaCO3 in agriculture (sibling (d)(i) was excluded as out-of-syllabus); ceramics/refractory context (report.md says ceramics are out-of-syllabus, yet these are kept).',
    'Syllabus text search (no "monitor", "ceramic", "refractory", "agricultur" in the AS outcomes); item text.',
    'a91_selfcontained.py keyword scan + syllabus text search + reading',
    'Exclude the two IR-monitoring items and M/J 17/P21/Q3(d)(ii); for the three ceramics items decide (they test giant ionic lattice properties, 4.2) and make report.md consistent.', 'needs your choice')
add('A-012', 'Minor', '6 Crop quality', 'Visual sample: MAR 22/P22/Q1(c) (p35); M/J 16/P21/Q1(c) (p57); MAR 24/P22/Q3(d) (p162); O/N 21/P21/Q3(a)(i) (p243); M/J 21/P22/Q2(c)(i)-(ii) (p245); O/N 21/P23/Q4(a)(i)-(ii) (p955)',
    'Dotted answer lines still visible (lines drawn as vector dots are not whited out; only text-dot runs are). 6 of 330 sampled question items (~1.8%, est. ~30 in the book).',
    'Contact-sheet review; p35 zoom shows the dotted line with no text-layer dots under it.',
    'a110_sheets.py (visual)', 'Also white-out rows of regularly spaced vector dots (not inside tables).', 'automatic')
add('A-013', 'Minor', '6 Crop quality',
    f"O/N 21/P22/Q3(e)(v) (p{q('O/N 21/P22/Q3(e)(v)')}); O/N 21/P22/Q3(e)(iv) (p{q('O/N 21/P22/Q3(e)(iv)')}); O/N 23/P22/Q2(c) (p{q('O/N 23/P22/Q2(c)')}); M/J 19/P22/Q1(c) (p{q('M/J 19/P22/Q1(c)')}); M/J 26/P24/Q4(c) (p{q('M/J 26/P24/Q4(c)')}); M/J 26/P23/Q5(b)(i) (p{q('M/J 26/P23/Q5(b)(i)')})",
    'Text cut at a crop edge: a fragment of the previous part\'s "[2]" shown (Q3(e)(v)), mark brackets partly clipped ([2], [3]), axis labels cut at the left edge ("amount / mol", "transmittance").',
    'a71_clipped.py partial-word list; a77_marks_clipped.py; visual zoom of O/N 23/P22/Q2(c).',
    'a71_clipped.py, a77_marks_clipped.py, visual',
    'Pad band bottoms by ~2 pt below the last glyph; exclude a neighbour part\'s mark line; widen x-range for left-margin axis labels.', 'automatic')
add('A-014', 'Minor', '6 Crop quality',
    f"MAR 26/P22/Q4(d) (p{q('MAR 26/P22/Q4(d)')}-{q('MAR 26/P22/Q4(d)')+1}); MAR 16/P22/Q5(a)(i) (p1163-1164); M/J 22/P23/Q3(b) (p690-691); M/J 21/P23/Q4(c) (p1152-1153)",
    'Figure split across a page break (label "E" alone at the bottom of p661; table/structures broken over two pages).',
    'a82_page_split.py (ink crossing the cut on contiguous bands on different pages) + visual.',
    'a82_page_split.py, visual', 'Keep a figure band (with its labels) on one page; move it to the next page if it does not fit.', 'automatic')
add('A-015', 'Minor', '6 Crop quality', f"M/J 15/P22/Q1(d) answer (p538-539)",
    'Orphan MS row showing the printed question total "[18]" alone on near-blank page 539 (question totals should be trimmed; no [Total] in split items).',
    'Near-blank page scan (ink < 40 px) flags p539 only; render.',
    'a74_space.py, visual', 'Trim the printed question-total row from old-layout MS crops (as already done elsewhere).', 'automatic')
add('A-016', 'Minor', '9 Book structure', 'Whole book (1273 pages) and 22 unit PDFs',
    'No bookmarks/outline (0 TOC entries).', 'pymupdf get_toc() == []', 'a50_structure.py',
    'Add an outline: Contents, Unit n, Unit n Answers Section, Topic index, Appendix (optionally each item).', 'automatic')
add('A-017', 'Minor', '7 Self-containment', f"O/N 21/P21/Q4(c) (p{q('O/N 21/P21/Q4(c)')}); O/N 21/P23/Q4(c) (p{q('O/N 21/P23/Q4(c)')})",
    'Items that say "Use the Data Booklet to identify the functional group" are kept, although the AUTO-DECIDED rule excluded Data-Booklet items (e.g. sibling Q4(b)).',
    'Item text contains "Data Booklet".', 'a91_selfcontained.py',
    'Apply the rule consistently (see Decision D4).', 'needs your choice')
add('A-018', 'Minor', '7 Self-containment',
    f"MAR 18/P22/Q2(c)(iv) (p{q('MAR 18/P22/Q2(c)(iv)')}); MAR 19/P22/Q2(d)(ii) (p{q('MAR 19/P22/Q2(d)(ii)')}); O/N 18/P21/Q3(a)(iii) (p{q('O/N 18/P21/Q3(a)(iii)')}); O/N 18/P23/Q3(a)(iii) (p{q('O/N 18/P23/Q3(a)(iii)')})",
    'Dangling references to a sibling sub-part that is not shown; answerable anyway (fallback value given, or the reference is incidental), but CLAUDE.md says never leave a dangling reference.',
    'Reference without the sibling label present.', 'a92_roman_refs.py',
    'Add the sibling as context (or merge items).', 'automatic')
add('A-019', 'Minor', '13 Report accuracy', 'report.md, SUMMARY.md, cover',
    'Narrative claims that are not true: "Self-containment re-check: 0 failures" (see A-010/A-018); "Fixed ... download-site watermark, corner marks/barcode stubs" (A-005/A-006); exclusion reasons for M/J 15/P21, M/J 16/P23, O/N 16/P21/P23 and the typo cases (A-007..A-009); MAR 19/P22/Q1(d) listed as an AUTO-DECIDED tie although it is excluded. All counts (papers, questions, items, per-unit items/marks, pages, sizes) are correct.',
    'Counts re-measured from the book; claims compared with findings.', 'a40_threeway.py, manual comparison',
    'Regenerate report.md/SUMMARY.md after fixes.', 'automatic')
add('A-020', 'Minor', '10 Text layer', 'Whole book',
    'Hidden text: 2,495 dotted answer-line runs remain in the text layer under white rectangles, so copying item text yields "......" noise. No items.jsonl exists and work/items_phase*.json carry no text, so "items.jsonl text matches PDF" cannot be verified.',
    'a75_dots.py (dot runs with no ink under them).', 'a75_dots.py',
    'Redact (not overlay) answer-line glyphs; optionally emit items.jsonl with each item\'s text.', 'automatic')
add('A-021', 'Minor', '8 Topics', f"{len(dis)} items (list in audit/out/tag_compare.json)",
    f'My blind re-tag disagrees with the build unit on {len(dis)} of 1,577 judged items (94.1% agreement; 158 not judged). 11 disagreements checked against the full item text: the build was right or defensible in all 11, so these are review suggestions, not errors. topics.json justifications cite the section (e.g. "9.2 ...") but not the learning-outcome number.',
    'audit/out/my_tags.txt vs index.csv.', 'a100_owntext.py, a101_compare_tags.py, manual reading',
    'No change needed; optionally add learning-outcome numbers (e.g. 9.2.3) to justifications.', 'needs your choice')
add('A-022', 'Cosmetic', '7 Self-containment', fmt(dup),
    'Figure 4.1 printed twice (once in the stem, again as "Context: Fig. 4.1").', 'Same caption line twice in item text.',
    'a90_itemtext.py caption count', 'Skip a figure context block when the stem crop already contains it.', 'automatic')
add('A-023', 'Cosmetic', '6 Crop quality', f"M/J 18/P22/Q4(d)(ii)-(iii) (p{q('M/J 18/P22/Q4(d)(ii)-(iii)')}); M/J 16/P21/Q5(d) (p{q('M/J 16/P21/Q5(d)')}); MAR 23/P22/Q4(d) (p{q('MAR 23/P22/Q4(d)')})",
    'Source navigation text kept: "Question 4 continues on page 10", "Question 5 continues..."; "Table 4.1 (on page 14)" refers to source pagination.',
    'Text-layer search.', 'a90_itemtext.py + grep', 'Drop "continues on page" lines.', 'automatic')
add('A-024', 'Cosmetic', '6 Crop quality', f"M/J 26/P24/Q1(c) (p{q('M/J 26/P24/Q1(c)')})",
    'Unneeded context: Figure 1.3 (AlCl4- dot-and-cross) attached although (c) refers only to Figure 1.2.', 'Visual.', 'visual',
    'Only attach figures the part text references.', 'automatic')
add('A-025', 'Cosmetic', '6 Crop quality', '94 pages (list in audit/out/space.json)',
    'Large trailing white space (>350 pt) on 94 item pages because items never split; e.g. p8, p14, p23.', 'Pixel scan.', 'a74_space.py',
    'Optional: allow splitting long items at part boundaries.', 'needs your choice')
add('A-026', 'Cosmetic', '10 File', 'Book + unit PDFs',
    '42 font instances not embedded (Arial/Times/Symbol inherited from source PDFs such as 9701_s26_*.pdf, plus base-14 Helvetica for headers). qpdf --check passes; all pages A4; all files < 95 MB.',
    'pdffonts; qpdf --check rc=0; pdfinfo page sizes.', 'a60_file.sh', 'None required.', 'needs your choice')

# Decisions on layout vs the Physics reference
add('A-027', 'Major', 'Physics reference', 'All 1,735 items',
    'Reference style differs from the target "M/J 25/P22/Q5/b": the book uses "Q5(b)" (1,656), "Q5(b)(ii)" (1,386 incl. answers), "Q3(b)(ii)-(iii)" (205 items) and "Q3(a)-(c)" (9 items).',
    'Heading parse of all 3,470 headings.', 'a30_book_items.py', 'Rewrite headings to Q5/b, Q5/b(ii), Q3/b(ii,iii), Q3/a,b,c (see D1).', 'needs your choice')
add('A-028', 'Major', 'Physics reference', '1,566 question items; 23 answers',
    'Generated "Context" labels (7 variants, e.g. "Context: part (b) (introduction)") and "Answer for context part (x)" labels; the Physics booklet shows stem and figures inline with no label.',
    'Item text lines starting with "Context".', 'a90_itemtext.py', 'Remove labels and the left rule; keep the crops inline (see D2).', 'needs your choice')
add('A-029', 'Minor', 'Physics reference', '353 runs covering 865 items',
    'Adjacent parts of the same question filed in the same unit are separate items, each repeating stem and figures (e.g. O/N 16/P21/Q1(a)...(h) = 8 items in Unit 2; M/J 25/P21/Q5(a),(b),(c)(i) in Unit 18). The Physics booklet groups kept parts in one item ("Q2/a,b").',
    'Consecutive items in a unit from the same paper+question.', 'audit script inline (book_items.json)', 'Merge such runs into one item with one stem (see D3).', 'needs your choice')
with open('audit/findings.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(F[0].keys())); w.writeheader(); [w.writerow(r) for r in F]
from collections import Counter
print(len(F), 'findings', Counter(r['severity'] for r in F))
