# Audit report: Chemistry 9701 Paper 2 topical workbook

- **Audited:** branch `claude/topical-past-paper-booklets-jdm9la` @ `8816ea4`, which contains `Δ-chemistry/booklets/p2-topical-workbook/` (book PDF with 1,273 pages, 22 unit PDFs, `index.csv`), `topics.json`, `report.md`, `SUMMARY.md`, `state.json` and `work/`.
- **Audit branch:** `audit-report`. Everything is under `/audit/`: `findings.csv`, `scripts/` (every check), `out/` (machine-readable evidence).
- **Changes made:** none to the book, data, scripts or any existing file.
- **Independence:** none of the build's checkers (`hub/scripts/*.py`, `work/final_checks.json`) were reused. `topics.json` and `state.json` were not used as ground truth. Questions, parts, marks and mark-scheme (MS) rows were re-derived from the source PDFs in `data/` with new parsers (`a20`, `a21`). Crop placement was re-derived from the book PDF's own Form XObjects (BBox clip + source page; `a70`). The build's records were used only for the comparisons reported below.
- **Note on `items.jsonl`:** this file does not exist. The equivalent records are `work/items_phase1.json` and `work/items_phase2.json` (1,735 records, with no text).

## 1. Summary

| # | Check | Status | Items checked | Failures |
|---|---|---|---|---|
| 1 | Source | **FAIL** | 166 files (83 papers × QP+MS); 10 random re-downloads | 1 wrongful whole-paper exclusion with a false reason (M/J 15/P21, A-007). All 166 files are present. 165/166 page-1 headers match; s20 MS v23 says "Paper 3" (excluded per rule, D5). 10/10 re-downloads are byte-identical (SHA-256). No paper is silently missing. |
| 2 | Paper level | **FAIL** | 83 QPs; 369 questions | QP side: 83/83 pass (each question once, part marks = [Total], totals = 60). MS side: my parser agrees with 14 of the build's 23 question exclusions. 6 questions were wrongly excluded (A-008), 2 were excluded only because of an MS label typo (A-009), and the whole M/J 15/P21 paper was wrongly excluded (A-007). |
| 3 | Coverage | PASS* | 2,999 lowest-level parts in 83 papers | 2,648 parts appear exactly once; 0 duplicates; 0 missing without a stated reason. *The stated reasons are wrong for 75 + 31 parts (A-007, A-008, A-009). |
| 4 | Three-way consistency | PASS | 1,735 items × (book, `index.csv`, `items_phase*.json`, 22 unit PDFs) | 0 differences in item set, unit, order or page. The answers' numbering and order equal the questions'. `index.csv` rows are sorted by paper, not by book order (by design). |
| 5 | Marks and MS crops | PASS | 1,735 items | Item marks = my QP marks: 1,735/1,735. MS marks agree wherever my parse resolves the part. MS crops: 0 truncated or wrong rows in the 2017+ layouts. In the 2015–16 layouts the automated check was inconclusive (parser limits), so 3 items were checked by eye (all fine). |
| 6 | Crop quality | **FAIL** | All 16,488 placed crop bands (automated); 440 items by eye | 1 Critical (A-001, 6 items), 4 Major classes (A-002–A-006, 51 items), Minor classes A-012–A-015 |
| 7 | Self-containment | **FAIL** | 1,735 question items | 4 items not answerable alone (A-010), 4 harmless dangling references (A-018), 2 items need the Data Booklet (A-017), 7 items show a figure twice (A-022). The stem is present in every item (0 missing). |
| 8 | Topics | PASS | 1,577 of 1,735 items re-tagged blind (91%) | 94.1% agreement; 93 disagreements, 11 of them checked in full text, all in the build's favour. 0 most-marks arithmetic errors; 10 ties, all consistent; all cited sections exist; no unit has fewer than 5 items (minimum 26); no empty units. |
| 9 | Book structure | **FAIL** | 1,273 pages | No bookmarks (A-016). Everything else passes: contents 46/46 page numbers correct; running header correct on 1,247/1,247 pages that have one; page numbering continuous; no Read & Write branding; numbering sequential per unit; newest-first order 0 violations; question/part order within a paper 0 violations; Periodic Table appendix present (from M/J 26/P24). |
| 10 | Text layer and file | PASS* | 23 PDFs | `qpdf --check` passes on all 23; all pages A4; largest file 39.6 MB; text on every page. *42 fonts not embedded (inherited from the sources; A-026); hidden dotted-line text in the text layer (A-020). The items-text comparison was NOT RUN (no item text exists). |
| 11 | Phase 2 | **FAIL** | 926 Phase-2 items (keyword scan); 36 exclusions reviewed | 6 items kept that are not clearly in the syllabus or contradict the stated exclusions (A-011). No wrong out-of-syllabus exclusion found. |
| 12 | AUTO-DECIDED log | Reviewed | 21 entries | 17 right; 2 partly wrong (old-MS heuristics caused A-008; the Data Booklet rule is applied inconsistently, A-017); 1 stale (MAR 19/P22/Q1(d) is listed as a tie but is excluded); 1 claim incomplete (the watermark is not fully removed, A-005) |
| 13 | Report accuracy | **FAIL** | Every count in `report.md`/`SUMMARY.md` | All counts are correct (81 papers, 337 questions, 1,735 items, 4,343 marks, per-unit items and marks, 1,273 pages, file sizes). 5 narrative claims are false (A-019). |
| — | Physics reference standard | Confirmed, with a caveat | PDF p280–281, p424 + answers p321, p462; 4 more partial items | Your 2 examples confirmed. The 4 other partial items found renumber the kept parts and drop the stem (see §3). |

**Visual review count:** 440 sampled items (15 question items + 5 answers per unit × 22 units, evenly spaced; `a110_sheets.py`), on 74 contact sheets, all viewed. On top of that, about 45 automated flags were rendered and compared with the source.

## 2. Findings

Fix type: "automatic" means a mechanical rebuild fix; "needs your choice" means you need to decide. The full rows, with every affected item, are in `findings.csv`.

### Critical

**A-001: Skeletal formulae altered by whitespace removal** (Critical; check 6; fix automatic)
- **Items:** M/J 22/P21/Q3(a) p688, Q3(b) p802, Q3(c)(i) p1013, Q3(c)(ii)-(iii) p803, Q3(d)(i)-(ii) p951–952, Q3(d)(iii) p486.
- **What's wrong:** the build drops source rows it thinks are blank. Those rows held the methyl and isopropyl branches of T (Fig. 3.1), Q and R (Fig. 3.3) and R (Fig. 3.4). The book shows unbranched or stub-branched molecules, which changes the chemistry: Q3(a) asks which stereoisomerism T shows. In Q3(d)(iii), Fig. 3.1 (wrong) and Fig. 3.2 (correct) contradict each other.
- **Evidence:** dropped strips with figure-only ink in `9701_s22_qp_21` p7 y100.3–126.4, p9 y113.6–139.8 and p9 y456.5–483.3 (`out/dropped_ink.json`). Book p688/p486 were rendered against source p7/p9.
- **Method:** `a80b_dropped_ink.py`, then visual comparison.
- **Proposed change:** when splitting bands, never drop a row that contains any non-dotted ink within the band's x-range; merge the neighbouring bands instead. Re-crop Figs. 3.1, 3.3 and 3.4 and rebuild the 6 items.

### Major

**A-002: Figure lines broken by white stripes (35 items)** (fix automatic)
- **Items:** M/J 16/P23/Q4(a),(b),(c),(d)(i),(d)(ii)-(iv) (p739, 975, 1235, 976, 739); M/J 18/P22/Q4(b),(c),(d)(i),(d)(ii)-(iii),(e) (p716, 1036, 1037, 717, 111); M/J 18/P23/Q4(c) p900; M/J 21/P23/Q4(a)(i),(a)(ii)-(iii),(b),(c) (p699, 1019, 957, 1152); M/J 22/P22/Q4(b)(i)-(ii) p690, Q4(b)(iii) p32, Q5(c)(i) p888; M/J 22/P23/Q3(a)(i),(a)(ii),(a)(iii),(a)(iv)-(v),(b),(c) (p176, 289, 369, 427, 690, 1015); MAR 17/P22/Q3(b) p908; MAR 21/P22/Q3(a)(i),(a)(ii),(b)(i),(b)(ii),(c),(d) (p293, 639, 374, 184, 1218, 1110); O/N 20/P21/Q4(c) p1020; O/N 20/P22/Q3(c)(iii) p814; O/N 20/P23/Q4(c) p1024; O/N 22/P22/Q3(d) p1149.
- **What's wrong:** bond lines (C–H, C=O, C–Br, C≡N), branch stubs and box edges are cut where rows were removed. Structures are still recognisable, but bonds look dashed or detached.
- **Evidence:** 53 dropped strips with figure-only ink in 41 items. Rendered against the source: structure G in M/J 22/P23/Q3 (p176 vs source p6), acetoin C=O in M/J 16/P23/Q4 (p739), R in MAR 21/P22/Q3 (p184).
- **Method:** `a80b_dropped_ink.py`, `a79_split_gaps.py`, visual.
- **Proposed change:** the same rule as A-001; rebuild the listed items.

**A-003: Fig. 4.2 truncated** (fix automatic)
- **Item:** M/J 23/P22/Q4(c)(iv)-(v), p425.
- **What's wrong:** the "Context: Fig. 4.2" block shows only the bottom half of the figure; the H3C–CH2–O⁺–H structures and the arrow are missing. Part (v) says "Use Fig. 4.1 and Fig. 4.2". A stray fragment of a "[2]" mark also shows.
- **Evidence:** source `9701_s23_qp_22` p9 vs book p425; the "[2]" mark is 31% inside the crop.
- **Method:** `a71`, `a72`, `a77`, visual.
- **Proposed change:** crop from the top of the figure to its caption, excluding the (c)(iii) mark line.

**A-004: Fig. 5.3 structure and spectrum label cut** (fix automatic)
- **Item:** M/J 25/P23/Q5(b)(v), p1186.
- **What's wrong:** the Fig. 5.3 context (structure of Z) has lost its O–CH3 line, so the ester O has nothing attached. The IR spectrum's y-axis label "transmittance / %" is cut at the left edge. The context is placed before the stem.
- **Evidence:** source `9701_s25_qp_23` p10 vs book; `a71` flags "transmittance" (hfrac 0.84).
- **Proposed change:** crop the full figure; allow x < 40 pt for labels in the left margin; order the context as stem, then figure.

**A-005: Footer and download-site logo inside 9 MAR 20/P22 items** (fix automatic)
- **Items:** Q1(d) p189, Q1(f) p376, Q1(g)(ii)-(iv) p295, Q2(c) p602, Q2(d)(ii) p602, Q3(a)(v) p1082, Q3(b)(ii) p248, Q3(c)(iii) p817–818, Q3(d)(ii) p818.
- **What's wrong:** "© UCLES 2020 9701/22/F/M/20 [Turn over" and the red PapaCambridge logo are printed in the items. This paper is scaled to 0.9, so the build's fixed footer cut-off misses it.
- **Method:** `a73_furniture.py`: footer text inside bands, plus a red-pixel scan (8 pages).
- **Proposed change:** detect the footer by its text, not by a fixed y position.

**A-006: Barcode, page number and corner mark mid-item** (fix automatic)
- **Items:** M/J 24/P22/Q1(d)-(e) p473, Q2(b) p279, Q3(b) p358, Q4(c) p1146.
- **What's wrong:** the top-of-page furniture of the next source page is included in the continuation crop.
- **Evidence:** page numbers "3", "5", "7", "8", "11" are 57% inside bands; renders of p279 and p1146.
- **Method:** `a73`, `a71`.
- **Proposed change:** start continuation bands below the page-number/barcode zone.

**A-007: Whole paper M/J 15/P21 wrongly excluded** (checks 1 and 2; fix automatic)
- **What's wrong:** `report.md` says "no questions found in QP text layer". In fact the QP has a normal text layer; its pages are A3-scaled (842×1191 pt), which broke the build's fixed coordinates.
- **Independent result:** Q1–Q4 each appear once; part sums equal the [Total]s 20/15/12/13; these sum to 60; the MS totals equal the QP totals for every question.
- **Method:** `a20`, `a21`, with coordinates normalised to page width.
- **Impact:** 27 parts missing from the book.
- **Proposed change:** normalise coordinates and include the paper (the Phase-2 syllabus filter still applies).

**A-008: Six questions wrongly excluded** (check 2; fix automatic)
- **Questions:** M/J 16/P23 Q2, Q3; O/N 16/P21 Q2, Q3; O/N 16/P23 Q2, Q3.
- **What's wrong:** they were excluded as "MS marks ≠ QP total", but the MS totals equal the QP totals. For example, O/N 16/P21 Q2 has part totals 3+1+1+1+2+3+2 = 13, matching [Total: 13] (`9701_w16_ms_21` p3 rendered). The build's old-layout reader double-counted the per-point marks.
- **Method:** `a21`, `a22`, `a23` (visual).
- **Impact:** 48 parts missing.
- **Proposed change:** fix the part-total column handling and include the questions.

**A-009: Exclusions caused by typos in MS row labels** (checks 2 and 5; needs your choice)
- **Affected:** O/N 23/P21 Q4 and O/N 23/P23 Q4 ("4(a(i)"); M/J 26/P24 Q5(e),(f) ("5f)"); M/J 18/P22 Q2(b),(c) ("2c(i)") and Q3(b),(c) ("3c(iii)"); MAR 19/P22 Q3(a) (labelled "3(e)").
- **What's wrong:** the marks match the QP in every case. `report.md` gives false causes ("MS marks 3/8/0"). The two (b) parts of M/J 18/P22 were excluded only as collateral of the neighbouring typo.
- **Evidence:** rendered MS rows (`9701_s26_ms_24` p22–23, `9701_s18_ms_22` p6/p8, `9701_m19_ms_22` p8).
- **Proposed change:** see Decision D6.

**A-010: Items that cannot be answered alone** (check 7; fix automatic)
- **Items:**
  - M/J 16/P22/Q4(b)(ii), p1092: "one of your esters in (i)".
  - M/J 16/P23/Q4(d)(ii)-(iv), p739: "the product in (i)".
  - O/N 19/P22/Q2(c)(ii), p103: "the amount of CO2 calculated in (i)".
  - O/N 22/P22/Q3(b), p1125: "D2" is defined only in Table 3.1 of part (a), which is not shown.
- **Method:** `a92_roman_refs.py`, `a91`, sheet review.
- **Proposed change:** add the referenced sub-part (or Table 3.1), with its MS row, as context, or merge with the sibling item.

**A-011: Phase-2 items outside the current syllabus** (check 11; needs your choice)
- **Items:** O/N 19/P21/Q3(a)(iv) p1221 and O/N 19/P23/Q3(a)(iv) p1223 (IR monitoring of atmospheric CO; 22.1 only requires analysing a spectrum); M/J 17/P21/Q3(d)(ii) p563 (use of CaCO3 in agriculture; its sibling (d)(i) was excluded as out-of-syllabus); M/J 15/P23/Q2(c) p257, M/J 19/P23/Q3(c) p251, MAR 17/P22/Q1(c)(ii) p256 (ceramics/refractory context, although `report.md` lists ceramics as out-of-syllabus).
- **Evidence:** none of "monitor", "ceramic", "refractory" or "agricultur" appears in the 2025–27 AS outcomes.
- **Proposed change:** exclude the first three. For the three ceramics items, see D7.

**A-027: Reference format differs from the target** (Physics reference; needs your choice)
- **What's wrong:** all 1,735 items use `Q5(b)`, `Q5(b)(ii)`, `Q3(b)(ii)-(iii)` (205 items) or `Q3(a)-(c)` (9 items). The target is `M/J 25/P22/Q5/b`.
- **Proposed change:** see D1.

**A-028: Generated "Context" labels** (Physics reference; needs your choice)
- **What's wrong:** 1,566 question items carry a "Context" label in 7 variants (e.g. "Context: part (b) (introduction)"). 23 answers carry "Answer for context part (x)". The Physics booklet shows the stem and figures inline with no label.
- **Proposed change:** see D2.

### Minor and Cosmetic (grouped)

| Group | Count | Examples (ref, page) | Proposed change |
|---|---|---|---|
| A-012 Visible dotted answer lines (vector dots, not whited out) | 6 of 330 sampled question items (~1.8%, est. ~30 in total) | MAR 22/P22/Q1(c) p35; MAR 24/P22/Q3(d) p162; O/N 21/P23/Q4(a)(i)-(ii) p955 | Also white out rows of regularly spaced vector dots outside tables |
| A-013 Text cut at a crop edge (marks, axis labels) | 6 items | O/N 21/P22/Q3(e)(v) p954 (fragment of the previous "[2]"); O/N 23/P22/Q2(c) p362 ("[3]" bottom cut); M/J 19/P22/Q1(c) p378 ("amount / mol" cut) | Pad bands about 2 pt; widen x-range for margin labels |
| A-014 Figure split across a page break | 4 items | MAR 26/P22/Q4(d) p661–662 (label "E" alone); MAR 16/P22/Q5(a)(i) p1163–1164 | Keep a figure with its labels on one page |
| A-015 Orphan MS question-total row "[18]" on a near-blank page | 1 | M/J 15/P22/Q1(d) answer p538–539 | Trim printed question totals |
| A-016 No bookmarks | whole book + 22 unit PDFs | — | Add an outline (units, Answers Sections, index, appendix) |
| A-017 Data-Booklet items kept despite the AUTO rule | 2 | O/N 21/P21/Q4(c) p1076; O/N 21/P23/Q4(c) p1078 | See D4 |
| A-018 Harmless dangling sibling references | 4 | MAR 18/P22/Q2(c)(iv) p112; O/N 18/P21/Q3(a)(iii) p438 | Add the sibling as context or merge |
| A-019 False narrative claims in `report.md`/`SUMMARY.md`/cover | 5 claims | "Self-containment 0 failures"; "watermark/barcode stubs fixed"; wrong exclusion reasons | Regenerate after fixes |
| A-020 Hidden text and no item-text records | 2,495 hidden dot runs | whole book | Redact answer-line glyphs; emit `items.jsonl` with text |
| A-021 Topic disagreements for optional review; justifications cite sections, not learning outcomes | 93 items | M/J 22/P22/Q1(a) (build 4 / me 3); MAR 25/P22/Q2(b) (1 / 10) | No change needed; optionally add learning-outcome numbers |
| A-029 Adjacent same-question items repeat the stem (Physics groups them as one item) | 353 runs, 865 items | O/N 16/P21/Q1(a)…(h) (8 items, Unit 2); M/J 25/P21/Q5(a),(b),(c)(i) | See D3 |
| A-022 Figure shown twice | 7 | M/J 26/P23/Q4(b) p930; Q4(c)(i)-(ii) p659 | Skip a figure block already in the stem |
| A-023 Source navigation text kept | 3 | "Question 4 continues on page 10" (M/J 18/P22/Q4(d)(ii)-(iii) p717) | Drop these lines |
| A-024 Unneeded context figure | 1 | M/J 26/P24/Q1(c) p149 (Fig. 1.3) | Attach only referenced figures |
| A-025 Large trailing white space (>350 pt) | 94 pages | p8, p14, p23 | Optional: split long items |
| A-026 Non-embedded fonts inherited from the sources | 42 | e.g. 9701_s26_* | None required |

## 3. Physics reference standard

**Confirmed by me** (`a01_sheet.py`, `a02_physics_strips.py`):

- **PDF p280–281 (printed 284–285):** item "2. M/J 23/P21/Q2/a,b". The stem and Fig. 2.1 appear inline with no label. The original letters (a), (b) are kept.
- **PDF p424 (printed 432):** item "9. MAR 21/P22/Q6,a,b(i,ii,iii)", with the same layout.
- **Answers Section** (PDF p321 for Unit 7 and p462 for Unit 10): the same item numbers, a bold reference, answers only for the kept parts, original letters, and marks at the right.

**4 more partial items I found** (all printed pages are PDF page + 4 to 8):

| Item | Question page (PDF) | Answer page (PDF) | Kept parts relabelled? | Stem shown? |
|---|---|---|---|---|
| O/N 19/P23/Q4(b) | p305 | p325 | yes: (b) shown as "(a)" | no |
| M/J 19/P22/Q2/(c,d) | p306 | p325 | yes: (c),(d) shown as "(a)","(b)"; the text still says "the car in (b)" | no |
| O/N 14/P22/Q1/b | p349 | p359 | yes: "(a)(i),(ii)" | no |
| MAR 21/P22/Q6,b(iv) | p479 | p513 | yes: "(a)(i)" | no |

So the Physics booklet is not consistent with itself. Your rule (keep the original letters; stem inline; reference `Q5/b`) matches the two examples you checked. It does not match these four, and the reference punctuation also varies (`Q2/a,b`, `Q6,a,b(i,ii,iii)`, `Q2/(c,d)`, `Q4(b)`, `Q1/b`).

**Where the Chemistry book differs from your stated standard:**
- Reference format: A-027.
- Generated "Context" and "Answer for context part" labels: A-028.
- Grouped "Q3(a)-(c)" and "(ii)-(iii)" ranges in place of `/a,b,c`: A-027.
- Separate items per part rather than one item per kept group: A-029.
- Extra blocks: duplicate Fig. 4.1 (A-022), an unneeded Fig. 1.3 (A-024), and the MS rows of context parts in answers (23 items).

The Chemistry book does keep the original letters (no renumbering found) and shows the stem in every item. Answers are official MS crops rather than retyped text; CLAUDE.md requires this.

## 4. Decisions needed

| ID | Decision | My recommendation |
|---|---|---|
| D1 | Reference style (A-027) | Use your target: `M/J 25/P22/Q5/b`, `Q5/b(ii)`, `Q3/b(ii,iii)`, `Q3/a,b,c`. Apply it to the question side, the answers, `index.csv` and `items.jsonl`. |
| D2 | Remove the generated "Context" / "Answer for context part (x)" labels and the left rule (A-028) | Yes. Show stem, figures and earlier parts inline as in the paper. Keep the MS rows of context parts only when the item depends on that part's answer. |
| D3 | Merge adjacent parts of one question filed in the same unit into one item with one stem (A-029, 865 items into 353) | Yes. It matches Physics, removes repetition, and also fixes the implicit dependencies (e.g. O/N 16/P21/Q1(f)-(h)). |
| D4 | Data Booklet items (A-017; 11 Phase-2 items excluded for this) | Keep them. The Data Booklet is the standard exam resource; add a one-line note "Data Booklet needed". If you prefer exclusion, apply it to O/N 21/P21/P23 Q4(c) too. |
| D5 | s20 v23: the MS page 1 says "Paper 3", although the code is 9701/23, the title is "AS Level Structured Questions" and the paper is out of 60 | Keep it excluded by rule, or accept it as a Cambridge typo. If accepted, my parse shows only Q2 failing (MS 14 vs QP 13), so Q1 and Q3–Q5 could be added. |
| D6 | Typo-tolerant MS label matching (A-009) | Accept a typo label only when it is unambiguous (a single unmatched row whose marks equal the QP part), and log each case. This recovers O/N 23/P21/P23 Q4, M/J 26/P24 Q5(e),(f), M/J 18/P22 Q2(b),(c), Q3(b),(c) and MAR 19/P22 Q3(a). |
| D7 | Ceramics/refractory context items (A-011) | Keep them: the question asks for giant ionic lattice properties (4.2). Remove "ceramics" from the out-of-syllabus wording in `report.md`. Exclude the IR-monitoring and agriculture items. |
| D8 | Tie rule (MAR 26/P22/Q4(d): the build used the first sub-part among the tied topics, not the literal first sub-part, which is topic 18 with 1 mark) | Keep the build's interpretation and state it in CLAUDE.md. |

## 5. Checks not run

| Check | Reason |
|---|---|
| `items.jsonl` text vs PDF text (10) | The file does not exist; `work/items_phase*.json` hold no text. |
| Full-book OCR of the Physics booklet | Tesseract took 3–9 minutes per page in this container (the 550-page run hit its time limit). Reference columns were tiled and read by eye instead (`a02_physics_strips.py`). |
| Automated MS-row truncation check for the 2015–16 MS layouts (5) | My parser's label reading for the separate-column layouts is unreliable (86 inconclusive flags). Replaced by visual checks of 3 items (all fine). |
| Topic re-tag of 158 items (9%) (8) | The item's own text was too short to judge without the full context (e.g. "Name X."). These were not judged. |
| Pixel-based detection of visible dotted lines across the whole book (6) | The detector gave too many false positives (text rows and table rules) and was dropped. The rate was estimated from the 330-item visual sample instead (A-012). |

## Appendix: scripts and evidence

| Script | Purpose | Evidence (`hub/audit/out/`) |
|---|---|---|
| `a10_sources.py`, `a11_redownload.py` | Expected-file list, page-1 header, SHA-256 re-download | `sources.json`, `redownload.json` |
| `a20_qp_parse.py`, `a21_ms_parse.py`, `a22_dbg.py`, `a23_msrow_img.py`, `a33_part_marks.py` | Independent QP/MS parsing; paper-level and part-level marks | `qp_parse.json`, `ms_parse.json`, `ms_q_mismatch.json`, `part_marks.json` |
| `a30_book_items.py`, `a31_coverage.py`, `a32_missing_vs_report.py` | Book headings; coverage against the source parts | `book_parse.json`, `book_items.json`, `coverage.json`, `missing_classified.json` |
| `a40_threeway.py` | Book / `index.csv` / items JSON / unit PDFs | `threeway_fail.json` (empty) |
| `a50_structure.py` | Contents, headers, numbering, order, bookmarks, appendix | `structure.json` |
| `a60_file.sh` | qpdf, fonts, page sizes, file sizes | `file_checks.txt` |
| `a70_bands.py` | Every placed crop (Form XObject BBox) mapped to its source page | `bands.json` |
| `a71`, `a72`, `a73`, `a74`, `a75`, `a77`, `a78`, `a79`, `a80b`, `a81`, `a82` | Clipped text, cut figures, furniture/logo, white space, hidden dots, cut marks, edge ink, dropped figure ink, side cuts, page splits | `clipped.json`, `cutfigs.json`, `furniture.json`, `space.json`, `dots_visible.json`, `marks_clipped.json`, `edge_ink.json`, `split_gaps.json`, `dropped_ink.json`, `side_cut.json`, `page_split.json` |
| `a80_marks_ms.py` | Item marks vs QP/MS; MS crop completeness and wrong rows | `marks_ms.json` |
| `a90_itemtext.py`, `a91_selfcontained.py`, `a92_roman_refs.py` | Item text; self-containment | `item_text.json`, `selfcontained.json`, `roman_refs.json`, `context_blocks.json` |
| `a100_owntext.py`, `a101_compare_tags.py` | Blind topic re-tag and comparison | `my_tags.txt`, `owntext.json`, `tag_compare.json` |
| `a110_sheets.py`, `a01_sheet.py`, `a02b_itemimg.py`, `a02_physics_strips.py` | Contact sheets and renders for visual review | `visual_sample.json` |
| `a120_findings.py` | Writes `findings.csv` from the evidence | `../findings.csv` |
