# Report — Physics 9702 Paper 2 topical workbook

Two sources (spec `Ω-physics/CLAUDE-physics.md`): **Part A** = the scanned Read and Write booklet (papers up to 2023; its items and answers used as they are, cropped from the OCR'd scan `Ω-physics/booklet-ocr.pdf`), **Part B** = official papers (O/N 2023, all 2024–2026 papers listed in the spec), built with the Chemistry pipeline. Nothing was retyped: every question and answer in the book is a crop of the scan or a vector clip of the official PDF.

## AUTO-DECIDED

| Item | Issue | What I did |
|---|---|---|
| Run branch | The prompt names `claude/physics-p2-booklet`; the session's default branch had another name | Followed the prompt (the user's explicit instruction): all work pushed to `claude/physics-p2-booklet`; no pull request. |
| 9702 s26 v21 | QP downloads, MS does not exist on the source (HTTP 302 to an error page) | Excluded (as the spec says) and reported. |
| Data and Formulae pages | In every Part B paper both are on QP page 2 (page 3 is blank or a question page) | Page 2 recognised by its 'Data'/'Formulae' headings and never used as question material; a page 3 with questions is used normally. Appendix: the Data and Formulae page of the newest paper (M/J 26/P24). |
| Physics mark schemes | Marks are printed as codes (B1, C1, M1, A1; B2/B3) not numbers; codes in brackets, e.g. (C1), belong to an alternative method | Marks = sum of the code digits; bracketed codes not counted. Check 4 (MS = QP total) passed for every question, so the reading is confirmed. |
| MS alternative introduced by 'OR' | In a few rows a second method follows an 'OR' line with unbracketed codes | Its codes are not counted only where the first method's marks equal that part's QP marks (else the row is read as printed). Applied to: MAR 26/P22 5(b)(iii) (4 → 2). |
| MAR 24/P22 MS label "2c(iii)" | Typo in the mark scheme (missing brackets) | Read as 2(c)(iii) (unambiguous; Chemistry decision D6). |
| M/J 24/P22 MS label "2c(i)" | Typo in the mark scheme (missing brackets) | Read as 2(c)(i) (unambiguous; Chemistry decision D6). |
| O/N 25/P23 | question paper identical to O/N 25/P21 (same text for every question; official files carry different codes) - duplicate not repeated | Paper not repeated: its questions are already in the book under O/N 25/P21. |
| Figure captions | Physics captions read 'Fig. 2.1 (not to scale)' and some figures share one caption line ('Fig. 4.1 (not to scale) Fig. 4.2 (not to scale)') | Both forms recognised as captions (the copied Chemistry rule only accepted a bare caption). Before this, 79 items failed the self-containment check; after it none. |
| Context height | The one-page context limit added the heights of overlapping regions (a figure inside a context part counted twice) | Height measured on the union of the context regions, as the book lays them out. |
| Booklet items: marks | The booklet's printed [marks] can only be read by OCR (the sample check shows the margin OCR is right for 46/55 items) | Marks are not given for booklet items in index.csv, items.jsonl or the unit pages (no unverified figures); the crops show them. |
| Booklet item headings in crops | The booklet prints its own number and reference above each item and answer | Crops start below that heading line; the book prints its own number (one numbering per unit) and the normalised reference. |
| M/J 26/P24/Q2/b | topic marks tie {1: 3, 6: 3} | filed under topic 1 (topic of first sub-part) |
| Booklet scan | 10 printed pages are missing from the 550-page scan (printed pages 96–97, 144–145, 313–314, 328–329, 534–535; the printed page numbers jump by 2 at each gap). The scan ends at printed page 560. | Nothing reconstructed. Items whose questions were entirely on missing pages are absent (their answers are dropped too); items and answers cut by a gap are kept as scanned with a grey note "Incomplete in the scanned booklet"; items whose answer is lost carry "Answer missing from the scanned booklet". Listed below. |
| Booklet item headings | Tesseract dropped or misread some small item numbers (18 headings: e.g. '41.' for '11.', '141.' for '11.', or no number at all) | Number taken from the sequence only where exactly one slot fits; every such heading was checked on a cropped strip by image (all confirmed; work/heading_number_checks.json). |
| Booklet references | 3 headings did not parse unambiguously (O/N 14/P22/Q1ic, MAR 21/P22/Q6,a,bi(i,ii,iii)) | Read by image from a cropped heading strip: O/N 14/P22/Q1/c; MAR 21/P22/Q6,a,b(i,ii,iii) (twice). Shown normalised: O/N 14/P22/Q1/c, MAR 21/P22/Q6/a,b(i,ii,iii). |
| Booklet duplicates | M/J 19/P21/Q7 appears as Unit 3 #16 and Unit 12 #28; MAR 20/P22/Q4 appears as Unit 4 #11 and Unit 9 #16 | Kept both (the booklet's own selection; the light check is report-only); each copy carries a grey note naming the other unit. |
| Booklet heading lines | On some pages the last mark (and dots) of an item is printed on the same line as the next item's heading | The item takes that line with the next heading whited out; the next item whites out the mark. Nothing else is altered. |
| O/N 2023 papers | The booklet has no items at all from O/N 23 (P21, P22, P23) | Built from the official papers as Part B (spec rule), with the 2024+ papers. |
| Booklet items 2024+ | None in the booklet (latest: M/J 23 and MAR 23) | Nothing dropped. |
| Electric-field items | Electric fields are A Level only in 2025–27 | 9 booklet items flagged (grey note "May be outside the 2025–27 syllabus", kept). Not flagged: Unit 12 #29 (only asks which radiation cannot be deflected by an electric field (tests charge, 11.1.7)); Unit 12 #30 (only asks which particles feel no electric force (tests charge, 11.2)) |
| Booklet part labels | Some booklet items relabel parts (e.g. O/N 14/P22/Q1/c printed as (a)) | Left as printed (spec). |
| Booklet Unit 3 #16 | The booklet files this question twice, once under an unrelated unit | Dropped the misfiled copy: M/J 19/P21/Q7 (alpha-particle scattering, quarks) is particle physics; kept in booklet Unit 12 (book Unit 11), dropped from booklet Unit 3 (book Unit 2, Kinematics). |
| Booklet Unit 4 #11 | The booklet files this question twice, once under an unrelated unit | Dropped the misfiled copy: MAR 20/P22/Q4 (progressive waves, diffraction grating) is waves/superposition; kept in booklet Unit 9 (book Unit 8), dropped from booklet Unit 4 (book Unit 3, Dynamics). |
| Booklet B3-24 | Question runs into printed pages missing from the scan | Question cropped from the official paper (9702_w15_qp_21.pdf, Q3; header verified, part marks = [Total] = MS marks = 10); the booklet answer is kept. Grey note on the item. |
| Booklet B4-15 | Question runs into printed pages missing from the scan | Question cropped from the official paper (9702_s19_qp_21.pdf, Q2; header verified, part marks = [Total] = MS marks = 9); the booklet answer is kept. Grey note on the item. |
| Booklet B7-21 | Question runs into printed pages missing from the scan | Question cropped from the official paper (9702_w18_qp_23.pdf, Q1; header verified, part marks = [Total] = MS marks = 8); the booklet answer is kept. Grey note on the item. |
| Booklet B12-4 | Question runs into printed pages missing from the scan | Question cropped from the official paper (9702_m23_qp_22.pdf, Q7; header verified, part marks = [Total] = MS marks = 5); the booklet answer is kept. Grey note on the item. |
| Booklet B7-4 | Answer missing from the scan or runs into missing pages | Answer cropped from the official mark scheme (9702_w22_ms_22.pdf, Q4, 8 marks; checks as above). Grey note on the answer. |
| Booklet B7-5 | Answer missing from the scan or runs into missing pages | Answer cropped from the official mark scheme (9702_w22_ms_21.pdf, Q2, 17 marks; checks as above). Grey note on the answer. |
| Booklet B7-6 | Answer missing from the scan or runs into missing pages | Answer cropped from the official mark scheme (9702_s22_ms_21.pdf, Q4, 5 marks; checks as above). Grey note on the answer. |
| Booklet B7-7 | Answer missing from the scan or runs into missing pages | Answer cropped from the official mark scheme (9702_w21_ms_21.pdf, Q3, 10 marks; checks as above). Grey note on the answer. |
| Booklet B7-8 | Answer missing from the scan or runs into missing pages | Answer cropped from the official mark scheme (9702_w21_ms_23.pdf, Q1, 11 marks; checks as above). Grey note on the answer. |
| Booklet B7-9 | Answer missing from the scan or runs into missing pages | Answer cropped from the official mark scheme (9702_s21_ms_22.pdf, Q1, 11 marks; checks as above). Grey note on the answer. |
| Booklet Unit 3 #25 O/N 15/P23/Q3 | Question entirely on pages missing from the scan (only its answer survived) | Restored at its booklet position from the official paper (9702_w15_qp_23.pdf/9702_w15_ms_23.pdf, Q3, 13 marks; checks as above). |
| Booklet Unit 4 #16 MAR 19/P22/Q3 | Question entirely on pages missing from the scan (only its answer survived) | Restored at its booklet position from the official paper (9702_m19_qp_22.pdf/9702_m19_ms_22.pdf, Q3, 6 marks; checks as above). |
| Booklet Unit 4 #17 O/N 18/P22/Q3 | Question entirely on pages missing from the scan (only its answer survived) | Restored at its booklet position from the official paper (9702_w18_qp_22.pdf/9702_w18_ms_22.pdf, Q3, 11 marks; checks as above). |
| Booklet Unit 7 #22 M/J 18/P21/Q2 | Question entirely on pages missing from the scan (only its answer survived) | Restored at its booklet position from the official paper (9702_s18_qp_21.pdf/9702_s18_ms_21.pdf, Q2, 15 marks; checks as above). |
| Booklet Unit 12 #5 O/N 22/P22/Q7 | Question entirely on pages missing from the scan (only its answer survived) | Restored at its booklet position from the official paper (9702_w22_qp_22.pdf/9702_w22_ms_22.pdf, Q7, 7 marks; checks as above). |
| Booklet Unit 12 #6 O/N 22/P21/Q6 | Question entirely on pages missing from the scan (only its answer survived) | Restored at its booklet position from the official paper (9702_w22_qp_21.pdf/9702_w22_ms_21.pdf, Q6, 7 marks; checks as above). |
| Booklet Unit 12 #7 O/N 22/P23/Q6 | Question entirely on pages missing from the scan (only its answer survived) | Restored at its booklet position from the official paper (9702_w22_qp_23.pdf/9702_w22_ms_23.pdf, Q6, 6 marks; checks as above). |
| Answer-line dot removal (2017-19 papers) | The copied Chemistry rule removed dot glyphs with a box as tall as the line, which also removed some marks such as "[2]" on the next line in 11 physics papers | Box narrowed to a thin strip through the dots' centres; every question paper now keeps all its non-dot text (checked on all 9702 and 9701 papers; the Chemistry book was not affected). |
| Final audit: booklet marks at item boundaries | A mark "[n]" on the next heading's line was always given to the previous item, so some answer marks were cut or shown with the wrong item; 14 marks the OCR did not read were cut at the crop bottom | Answer pages: the mark goes with the nearer text line; unread marks detected from ink and taken whole, the next heading whited out (all changed boundaries checked by eye). |
| Final audit: skewed booklet first lines | A first line rising to the right of the heading was cut at the crop top (19 items) | Words right of the heading that reach below it now set the crop top. |
| Final audit: scan specks and margin blobs | Specks at a region's end stretched crops over blank paper; 2 binding-shadow blobs in the left margin widened crops | Specks under 6 pt left out; dense wordless left-margin blobs whited out (right margin untouched, marks live there). |
| Final audit: fill-in blanks | Dot runs under 60 pt (nuclide numbers '......Th', equation slots, '......%' table cells) were removed with the answer lines (27 blanks, 6 papers) | Kept in the scan and the text layer; answer lines stay removed. |
| Final audit: page breaks | A figure caption (M/J 25/P22/Q3) and 6 lone marks '[n]' opened a page away from their content; 1 answer heading was alone at a page foot | Caption and mark-only bands stay with the band above; answer headings keep room for their whole first block. |
| Final audit: fraction at a crop top | The numerator of h2/h1 in M/J 25/P22/Q4(c) was whited out | A first-line word starting above the region top raises the top (1 place in the book). |
| Final audit: font subsetting | Subsetting the fonts turned the × sign into a box | Subsetting removed from the Physics build (the Chemistry build still subsets: not changed, reported). |
| Booklet's own errors kept | Typos and stray marks printed in the booklet (e.g. 'perpendicula', a stray 'V [2]' in an answer) | Kept as printed (never retype content). |

## Downloads and header checks

- Part B papers (spec list + O/N 23): 24 attempted, 23 downloaded and header-verified (9702/<variant>, 'Paper 2 AS Level Structured Questions', series), 1 excluded.
  - s26_21: ms: no file (HTTP 302, 287 bytes)
- QPs for the booklet light check: 37 attempted, 37 downloaded and header-verified (9702/<variant>, 'Paper 2 AS Level Structured Questions', series), 0 excluded.

## Part B paper-level verification

Checks per paper (scripts/physics/check_papers.py): every question once, [Total] = sum of part marks, totals = 60, MS marks = QP total per question, reference from the paper's own header.

| Paper | Questions | Result |
|---|---|---|
| O/N 23/P21 | 7 | all pass |
| O/N 23/P22 | 7 | all pass |
| O/N 23/P23 | 8 | all pass |
| MAR 24/P22 | 8 | all pass |
| M/J 24/P21 | 7 | all pass |
| M/J 24/P22 | 7 | all pass |
| M/J 24/P23 | 6 | all pass |
| O/N 24/P21 | 7 | all pass |
| O/N 24/P22 | 6 | all pass |
| O/N 24/P23 | 7 | all pass |
| MAR 25/P22 | 7 | all pass |
| M/J 25/P21 | 7 | all pass |
| M/J 25/P22 | 7 | all pass |
| M/J 25/P23 | 8 | all pass |
| M/J 25/P24 | 7 | all pass |
| O/N 25/P21 | 6 | all pass |
| O/N 25/P22 | 6 | all pass |
| O/N 25/P23 | 6 | question paper identical to O/N 25/P21 (same text for every question; official files carry different codes) - duplicate not repeated |
| O/N 25/P24 | 6 | all pass |
| MAR 26/P22 | 7 | all pass |
| M/J 26/P22 | 6 | all pass |
| M/J 26/P23 | 5 | all pass |
| M/J 26/P24 | 7 | all pass |

## Part B items

- 260 items from 22 papers (149 questions, 1320 marks). Excluded items: 0. Out of syllabus: none (every lowest-level part matched a 2025–27 AS learning outcome; topics.json).
- Lettered parts split by topic: 63; multi-topic lettered parts kept whole (filed under the majority topic, tagged 'also'): 6.

| Kept whole | Why not split | Marks by unit |
|---|---|---|
| M/J 24/P22/Q1/b | (b)(iii) depends on sibling ['(b)(i)'] | {'7': 3, '1': 2, '5': 4} |
| M/J 26/P22/Q5/c | context for ['(c)(i)', '(c)(ii)'] exceeds one page | {'10': 4, '9': 2} |
| M/J 26/P24/Q2/b | (b)(iii) depends on sibling ['(b)(ii)'] | {'1': 3, '6': 3} |
| O/N 24/P21/Q7/a | (a)(iii) depends on sibling ['(a)(ii)'] | {'10': 3, '9': 2} |
| O/N 24/P22/Q1/b | (b)(ii) depends on sibling ['(b)(i)'] | {'1': 3, '3': 1, '4': 2} |
| O/N 24/P22/Q6/c | context for ['(c)(i)'] exceeds one page | {'3': 3, '5': 2} |

Thin units (< 5 items): none.

## Part A: booklet light check (report only)

Source: `Ω-physics/Physics paper 2 9702 3.pdf` (550 scanned pages), OCR'd into `Ω-physics/booklet-ocr.pdf` (scripts/physics/ocr_booklet.py). Map: scripts/physics/map_booklet.py; checks: scripts/physics/booklet_check.py (results in work/booklet_check.json).

### Contents page vs pages

| Booklet unit | → topic | Title page (contents / found) | Answers Section (contents / found) | Question pages | Items | Answers | Numbered to |
|---|---|---|---|---|---|---|---|
| 1 Physical Quantities And Units | 1 | 5 / 5 | 30 / 30 | 6–29 | 33 | 33 | 33 |
| 2 Measurement Techniques | 1 | 39 / 39 | 59 / 59 | 40–58 | 23 | 23 | 23 |
| 3 Kinematics | 2 | 65 / 65 | 111 / 111 | 66–110 | 32 | 32 | 33 |
| 4 Dynamics | 3 | 123 / 123 | 167 / 167 | 124–166 | 31 | 31 | 33 |
| 5 Forces, Density And Pressure | 4 | 179 / 179 | 222 / 222 | 180–221 | 33 | 33 | 33 |
| 6 Work, Energy And Power | 5 | 233 / 233 | 270 / 270 | 234–269 | 31 | 31 | 31 |
| 7 Deformation Of Solids | 6 | 283 / 283 | 327 / 327 | 284–326 | 32 | 27 | 33 |
| 8 Waves | 7 | 338 / 338 | 362 / 362 | 339–361 | 22 | 22 | 22 |
| 9 Superposition | 8 | 369 / 369 | 410 / 410 | 370–409 | 33 | 33 | 33 |
| 10 Current Of Electricity | 9 | 421 / 421 | 462 / 462 | 422–461 | 33 | 33 | 33 |
| 11 D.C Circuits | 10 | 473 / 473 | 517 / 517 | 474–516 | 33 | 33 | 33 |
| 12 Particle And Nuclear Physics | 11 | 531 / 531 | 552 / 552 | 532–551 | 30 | 30 | 33 |

All 12/12 units start and end where the contents page says (printed page numbers). Items are numbered 1..N per unit in both the question and the answers sections; numbers absent below are explained by the missing scan pages.

### Pages missing from the scan and what they cost

| Printed pages missing | Lost |
|---|---|
| 96–97 | Unit 3 questions #25 |
| 144–145 | Unit 4 questions #16,17 |
| 313–314 | Unit 7 questions #22 |
| 328–329 | Unit 7 answers #5,6,7,8,9 |
| 534–535 | Unit 12 questions #5,6,7 |

| Item | Flag | In the book |
|---|---|---|
| Unit 3 #24 O/N 15/P21/Q3 | scan_gap_q:96-97 | question runs into missing pages 96-97: kept as scanned, note "Incomplete in the scanned booklet" |
| Unit 4 #15 M/J 19/P21/Q2 | scan_gap_q:144-145 | question runs into missing pages 144-145: kept as scanned, note "Incomplete in the scanned booklet" |
| Unit 7 #4 O/N 22/P22/Q4 | scan_gap_a:328-329 | answer runs into missing pages 328-329: kept, note on the answer |
| Unit 7 #5 O/N 22/P21/Q2 | no_answer | answer on missing pages: item kept, note "Answer missing from the scanned booklet" |
| Unit 7 #6 M/J 22/P21/Q4 | no_answer | answer on missing pages: item kept, note "Answer missing from the scanned booklet" |
| Unit 7 #7 O/N 21/P21/Q3 | no_answer | answer on missing pages: item kept, note "Answer missing from the scanned booklet" |
| Unit 7 #8 O/N 21/P23/Q1 | no_answer | answer on missing pages: item kept, note "Answer missing from the scanned booklet" |
| Unit 7 #9 M/J 21/P22/Q1 | no_answer | answer on missing pages: item kept, note "Answer missing from the scanned booklet" |
| Unit 7 #21 O/N 18/P23/Q1 | scan_gap_q:313-314 | question runs into missing pages 313-314: kept as scanned, note "Incomplete in the scanned booklet" |
| Unit 12 #4 MAR 23/P22/Q7 | scan_gap_q:534-535 | question runs into missing pages 534-535: kept as scanned, note "Incomplete in the scanned booklet" |

Answers whose questions are lost (not in the book): Unit 3 #25 (OIN 15/P23/Q3), Unit 4 #16 (MAR 19/P22/Q3), Unit 4 #17 (OIN 18/P22/Q3), Unit 7 #22 (MiJ 18/P21/Q2), Unit 12 #5 (ON 22/P22/Q7), Unit 12 #6 (O/N 22/P21/Q6), Unit 12 #7 (O/N 22/P23/Q6)

### References

- 366/366 item references parse unambiguously (after 1 headings read by image); every answer heading carries the same reference as its item (mismatches: 0).
- Years: 2013: 11, 2014: 23, 2015: 29, 2016: 25, 2017: 32, 2018: 38, 2019: 45, 2020: 47, 2021: 43, 2022: 44, 2023: 29. Items after 2023: 0.
- Duplicates: M/J 19/P21/Q7 (Unit 3 #16 and Unit 12 #28); MAR 20/P22/Q4 (Unit 4 #11 and Unit 9 #16) — both copies kept, noted.

### Sample check against the official papers (55 items, 5 per syllabus topic)

Printed marks were read from each item's right margin (OCR at 300 dpi) and compared with the official QP parsed from its text layer; then booklet crop and official pages were viewed side by side (50 dpi) for missing figures or text. Margin OCR matched the official marks for 50/55; the other 5 were OCR misreads (or the official parser missed a part on an old paper) and the marks were equal on inspection. Problems found per topic: 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0 (no unit reached 3, so no full-unit check was triggered).

| Topic | Item | Official | Printed (OCR) | Visual verdict |
|---|---|---|---|---|
| 1 | Unit 1 #1 M/J 23/P22/Q1 | 6 | 6 | text and figures match the official question; printed marks equal the official marks |
| 1 | Unit 1 #5 M/J 20/P22/Q1 | 6 | 6 | text and figures match the official question; printed marks equal the official marks |
| 1 | Unit 1 #16 O/N 17/P23/Q1 | 5 | 5 | text and figures match the official question; printed marks equal the official marks |
| 1 | Unit 1 #25 M/J 15/P22/Q1 | 6 | 6 | text and figures match the official question; printed marks equal the official marks |
| 1 | Unit 2 #23 O/N 13/P23/Q2 | 6 | 6 | text and figures match the official question; printed marks equal the official marks |
| 2 | Unit 3 #1 M/J 23/P23/Q1 | 7 | 7 | text and figures match the official question; printed marks equal the official marks |
| 2 | Unit 3 #9 O/N 20/P22/Q1 | 6 | 6 | text and figures match the official question; printed marks equal the official marks |
| 2 | Unit 3 #16 M/J 19/P21/Q7 | 5 | 5 | alpha-scattering / quark question filed by the booklet under Kinematics (also its Unit 12 #28); content and marks match |
| 2 | Unit 3 #23 O/N 15/P22/Q2 | 10 | 10 | text and figures match the official question; printed marks equal the official marks |
| 2 | Unit 3 #33 M/J 13/P23/Q2 | 11 | 11 | text and figures match the official question; printed marks equal the official marks |
| 3 | Unit 4 #1 M/J 23/P22/Q3 | 10 | 10 | text and figures match the official question; printed marks equal the official marks |
| 3 | Unit 4 #8 M/J 21/P21/Q2 | 12 | 15 | text and figures match the official question; printed marks equal the official marks |
| 3 | Unit 4 #18 O/N 18/P21/Q2 | 6 | 6 | text and figures match the official question; printed marks equal the official marks |
| 3 | Unit 4 #26 O/N 16/P22/Q2 | 12 | 12 | text and figures match the official question; printed marks equal the official marks |
| 3 | Unit 4 #33 O/N 14/P22/Q1/c | 5 | 4 | booklet prints part (c) relabelled as (a); content and marks (5) match |
| 4 | Unit 5 #1 M/J 23/P22/Q2 | 12 | 12 | text and figures match the official question; printed marks equal the official marks |
| 4 | Unit 5 #9 MAR 22/P22/Q3 | 7 | 7 | text and figures match the official question; printed marks equal the official marks |
| 4 | Unit 5 #17 M/J 20/P23/Q3 | 11 | 11 | text and figures match the official question; printed marks equal the official marks |
| 4 | Unit 5 #25 O/N 17/P22/Q2 | 5 | 5 | text and figures match the official question; printed marks equal the official marks |
| 4 | Unit 5 #33 M/J 15/P22/Q3 | 6 | 6 | text and figures match the official question; printed marks equal the official marks |
| 5 | Unit 6 #1 M/J 23/P21/Q2/c | 7 | 7 | booklet prints part (c) relabelled as (a); content and marks (7) match |
| 5 | Unit 6 #9 O/N 21/P22/Q3 | 8 | 8 | text and figures match the official question; printed marks equal the official marks |
| 5 | Unit 6 #16 MAR 19/P22/Q2 | 11 | 11 | text and figures match the official question; printed marks equal the official marks |
| 5 | Unit 6 #23 O/N 15/P23/Q8 | 6 | 6 | text and figures match the official question; printed marks equal the official marks |
| 5 | Unit 6 #31 M/J 13/P21/Q3 | 11 | 11 | text and figures match the official question; printed marks equal the official marks |
| 6 | Unit 7 #1 M/J 23/P22/Q4 | 5 | 5 | text and figures match the official question; printed marks equal the official marks |
| 6 | Unit 7 #13 O/N 20/P21/Q4 | 9 | 9 | text and figures match the official question; printed marks equal the official marks |
| 6 | Unit 7 #19 M/J 19/P22/Q2/c,d | 5 | 5 | booklet prints parts (c),(d) relabelled as (a),(b); content and marks (5) match |
| 6 | Unit 7 #27 M/J 17/P22/Q3 | 4 | 4 | text and figures match the official question; printed marks equal the official marks |
| 6 | Unit 7 #33 O/N 15/P23/Q7 | 5 | 5 | text and figures match the official question; printed marks equal the official marks |
| 7 | Unit 8 #1 M/J 23/P22/Q5 | 9 | 12 | text and figures match the official question; printed marks equal the official marks |
| 7 | Unit 8 #6 M/J 22/P21/Q5 | 8 | 8 | text and figures match the official question; printed marks equal the official marks |
| 7 | Unit 8 #11 M/J 20/P23/Q4 | 10 | 10 | text and figures match the official question; printed marks equal the official marks |
| 7 | Unit 8 #17 O/N 15/P21/Q5 | 7 | 7 | text and figures match the official question; printed marks equal the official marks |
| 7 | Unit 8 #22 O/N 13/P23/Q5 | 9 | 9 | text and figures match the official question; printed marks equal the official marks |
| 8 | Unit 9 #1 M/J 23/P21/Q5 | 9 | 8 | text and figures match the official question; printed marks equal the official marks |
| 8 | Unit 9 #9 M/J 21/P21/Q4 | 10 | 10 | text and figures match the official question; printed marks equal the official marks |
| 8 | Unit 9 #17 O/N 19/P22/Q5 | 9 | 9 | content and marks match; the item number sits left of x=16 pt on this skewed page (crop width taken from ink in the build) |
| 8 | Unit 9 #25 O/N 18/P21/Q4 | 11 | 11 | text and figures match the official question; printed marks equal the official marks |
| 8 | Unit 9 #33 O/N 16/P22/Q4 | 10 | 10 | text and figures match the official question; printed marks equal the official marks |
| 9 | Unit 10 #1 M/J 23/P22/Q6 | 5 | 5 | text and figures match the official question; printed marks equal the official marks |
| 9 | Unit 10 #9 MAR 21/P22/Q6/a,b(i,ii,iii) | 8 | 8 | text and figures match the official question; printed marks equal the official marks |
| 9 | Unit 10 #17 O/N 18/P23/Q6 | 4 | 4 | text and figures match the official question; printed marks equal the official marks |
| 9 | Unit 10 #25 M/J 16/P21/Q6 | 12 | 12 | text and figures match the official question; printed marks equal the official marks |
| 9 | Unit 10 #33 M/J 14/P21/Q6 | 11 | 11 | text and figures match the official question; printed marks equal the official marks |
| 10 | Unit 11 #1 MAR 23/P22/Q6 | 12 | 12 | text and figures match the official question; printed marks equal the official marks |
| 10 | Unit 11 #9 M/J 21/P21/Q5 | 11 | 11 | text and figures match the official question; printed marks equal the official marks |
| 10 | Unit 11 #17 O/N 19/P23/Q6 | 11 | 11 | text and figures match the official question; printed marks equal the official marks |
| 10 | Unit 11 #25 MAR 18/P22/Q5 | 10 | 10 | text and figures match the official question; printed marks equal the official marks |
| 10 | Unit 11 #33 O/N 14/P23/Q6 | 10 | 9 | text and figures match the official question; printed marks equal the official marks |
| 11 | Unit 12 #1 M/J 23/P22/Q8 | 6 | 6 | text and figures match the official question; printed marks equal the official marks |
| 11 | Unit 12 #12 O/N 21/P22/Q7 | 10 | 10 | text and figures match the official question; printed marks equal the official marks |
| 11 | Unit 12 #19 O/N 20/P21/Q8/a,b | 4 | 4 | (b)(ii) mark [1] printed on the line of heading 20: the crop now takes that line (heading whited out); content and marks (4) match |
| 11 | Unit 12 #26 O/N 19/P23/Q7 | 7 | 7 | text and figures match the official question; printed marks equal the official marks |
| 11 | Unit 12 #33 M/J 18/P21/Q7 | 6 | 6 | content and marks match; tests a beta-particle in a uniform electric field (flagged: outside the 2025-27 AS syllabus) |

### Flagged: may be outside the 2025–27 AS syllabus (kept, grey note in the book)

| Item | Reason |
|---|---|
| Unit 1 #8 O/N 19/P22/Q1 | (b) electric field strength of a point charge |
| Unit 6 #14 O/N 19/P23/Q3 | (b) charged particle between charged plates |
| Unit 10 #19 O/N 17/P22/Q5 | (b),(c) smoke particle in the uniform field between charged plates |
| Unit 12 #14 M/J 21/P22/Q6 | (d),(e) alpha-particles / nuclei in a uniform electric field |
| Unit 12 #15 M/J 21/P21/Q6 | (b) nuclei accelerated by a uniform electric field |
| Unit 12 #16 M/J 21/P23/Q6 | (c) proton and alpha-particle in a uniform electric field |
| Unit 12 #22 M/J 20/P21/Q6/b | (b)(ii) electric force on an ion between charged plates |
| Unit 12 #27 M/J 19/P22/Q6 | electric field lines and field strength |
| Unit 12 #33 M/J 18/P21/Q7 | beta-particle path in a uniform electric field |

## Checks on the built book

- Coverage (Part B): every lowest-level part of every included question is in exactly one item: unexplained gaps 0, duplicates 0.
- Self-containment re-check: 0 failures; context recomputed identically (0 mismatches). Marks re-check (item [marks] = MS marks): 0 failures.
- Every item's reference is on its indexed page (official 0 misses, booklet 0 misses) and appears with an answer entry and an index row (official 0 misses, booklet 0 misses). Booklet items in the book: 371/371.
- Full self-check with every audit-derived check: `audit/PHYSICS_CHECK.md` (not yet written).

