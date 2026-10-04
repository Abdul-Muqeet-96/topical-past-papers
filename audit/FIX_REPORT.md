# Fix report — approved audit findings

Branch `claude/audit-fixes` (from `audit-report`). Approved: every finding except A-021, A-025, A-026; decisions D1–D8 as recommended. Method: fix the build pipeline, rebuild everything from the source PDFs, then re-run the build's own checks and the independent audit scripts (`audit/scripts`). The original audit results stay unchanged on the `audit-report` branch.

## Book before → after

| | Before | After |
|---|---|---|
| Papers included | 81 | 82 (M/J 15/P21 added) |
| Questions excluded | 23 | 14 |
| Items / marks | 1,735 / 4,343 | 1,266 / 4,596 (fewer items because of D3 merging; more marks because of recovered parts) |
| Leaves covered (audit parse) | 2,648 | 2,774; all 63 missing leaves are out-of-syllabus with stated reasons |
| Pages / size | 1,273 / 39.6 MB | 1,159 / 29.6 MB |

## Findings

| ID | Status | What changed / evidence |
|---|---|---|
| A-001 Critical | Fixed | Crops are now found from rendered ink, so rows with ink are never dropped; figure blocks are grown over ink. The T/Q/R branches are restored (book p629, p728, p451, viewed). |
| A-002 | Fixed | Same rule. The audit's dropped-ink check on the question side went from 53 to 0. |
| A-003 | Fixed | M/J 23/P22 Fig. 4.2 is complete (p400, viewed). |
| A-004 | Fixed | Fig. 5.3 is complete; the clip widens to the margins when ink is there; context follows paper order (p1066–1067, viewed). |
| A-005 | Fixed | Scaled papers are normalised to A4, so the footer rule works and the logo falls off-page. Audit furniture check: 0 (was 14 bands, 9 logo pages). One remaining "red pixel" page (p203) is the mark scheme's own red dot-and-cross dots. |
| A-006 | Fixed | The page top is set below the page number, barcode and corner marks; bottom barcode and corner marks are whited out. |
| A-007 | Fixed | M/J 15/P21 included (A3 page normalised); 27 parts tagged. |
| A-008 | Fixed | The old mark-scheme reader now handles "[max N]" and the part-total column ("1+1"). M/J 16/P23, O/N 16/P21 and O/N 16/P23 Q2–Q3 are included, plus O/N 16/P22 Q4 (same cause; checked by eye: 4(a)(ii) "1+1" = 2, total 17). Every mark-scheme row of all 83 papers was diffed before and after; only the intended rows changed. |
| A-009 / D6 | Fixed | Tolerant labels and an unambiguous relabel rule; 15 typo cases are logged in report.md (including 2 more found: MAR 24/P22 4(c)(iv)→(iii) and M/J 20/P22 5(b)(iii)→5(c), both checked by eye). |
| A-010 | Fixed | References like "in (i)" were never resolved (a placeholder bug); labels such as "D2" are now detected. The 4 items now include the parts they depend on. Audit dangling part references: 3 → 0 real (1 flag remaining is a false positive, see below). |
| A-011 / D7 | Fixed | O/N 19/P21 and P23 Q3(a)(iv) and M/J 17/P21 Q3(d)(ii) are out-of-syllabus; ceramics items kept; report wording corrected. |
| A-012 | Fixed | Dotted rows are whited out. Audit visible dotted lines: 101 → 0. |
| A-013 | Fixed | Bands cover full word boxes; text straddling a region edge is completed or whited out. Audit clipped marks outside the re-scaled papers: 2 left (see residuals). |
| A-014 | Fixed | Figure/table bands stay on one page. Audit page-break splits on the question side: 0 (was 2). |
| A-015 | Fixed | An orphan question-total segment is dropped. |
| A-016 | Fixed | 47 bookmarks in the book; 2 per unit PDF. |
| A-017 / D4 | Fixed | 17 items kept with a "Data Booklet needed" note. |
| A-018 | Fixed | Sibling sub-parts are added as context. Audit dangling roman references: 0. |
| A-019 | Fixed | report.md and SUMMARY.md regenerated; false statements corrected and all D1–D8 decisions logged. |
| A-020 | Fixed | Answer-line dots are removed from the text layer itself. The hidden dot runs found in the book (46) are all on the answer side, because mark-scheme PDFs are not redacted. `items.jsonl` is written with each item's question text. |
| A-022 | Fixed | Items are the union of their source regions, so nothing is shown twice. |
| A-023 | Fixed | "continues on page" lines are whited out. "(on page 14)" inside sentences is left as printed. |
| A-024 | Fixed | M/J 26/P24 Q1(c),(d) is now one item (D3), so Figure 1.3 belongs to it. |
| A-027 / D1 | Fixed | All 2,532 headings use `Q5/b`, `Q5/b(ii)`, `Q3/b(ii,iii)`, `Q3/a,b,c`; 0 old-style ranges. |
| A-028 / D2 | Fixed | 0 "Context" or "Answer for context part" labels. Context MS rows are shown only where the item uses that part's answer (2 items). |
| A-029 / D3 | Fixed | No question has more than one item in the same unit; 0 merge fallbacks. |
| D5 | Applied | s20 v23 kept excluded. |
| D8 | Applied | Tie rule written into CLAUDE.md. |
| A-021, A-025, A-026 | Not approved | Unchanged. |

CLAUDE.md and layout.md are updated to state D1–D4 and D8.

## Re-run of the failed checks (audit scripts)

| Check | Before | After |
|---|---|---|
| 1 Source | FAIL (M/J 15/P21) | PASS: included |
| 2 Paper level | FAIL | PASS. The build excludes 14 questions; the audit parser agrees on all 14. It also flags O/N 16/P22 Q4, which is checked by eye as a parser limit ("1+1"). |
| 3 Coverage | PASS* | PASS: 2,774 covered, 0 duplicates, 63 missing all with stated reasons |
| 4 Three-way | PASS | PASS: 1,266 items in the book, index.csv, items json and answers; 0 differences |
| 6 Crops | FAIL | PASS with residuals: furniture 0, visible dotted lines 0, question-side dropped ink 0, question-side page splits 0 (see residuals) |
| 7 Self-containment | FAIL | PASS: 0 dangling references (one remaining flag, MAR 24/P22/Q2/d(i) "Fig. 2.2", is a false positive: the caption shares a line with "[4]"; viewed p720) |
| 9 Structure | FAIL (bookmarks) | PASS: contents 46/46, headers OK, 47 bookmarks |
| 10 File | PASS* | qpdf OK, all pages A4, largest file 29.6 MB |
| 11 Phase 2 | FAIL | PASS (D7 applied) |
| 13 Report accuracy | FAIL | Regenerated; build checks 0 failures in every category |
| Physics style | — | References, labels and merging as above |

## Residuals (not fixed; reported)

- **Audit coordinate mapping on the 7 re-scaled papers** (s15 v21, m20, s21 v21–23, w19 v21, w20 v21): 2,082 "clipped" and 186 "mark clipped" flags come from the audit's approximate raw-coordinate mapping (a constant ~0.85 overlap). Rendered items from these papers (e.g. p32) show no cut text.
- **Outside the re-scaled papers:** 19 question-side clipped-word flags. 15 of them are the next part's words, now whited out (p642, viewed clean). The others are a barcode glyph, one "_", and two "[2]" marks. On p866 a faint two-dot residue of the previous part's "[2]" is still visible at the right edge (cosmetic).
- **"Cut figure" flags (104 question-side):** a path's bounding box crosses a band gap where the source has no ink, i.e. empty answer space is compressed (e.g. M/J 24/P22/Q4/a,e on p625: a dashed divider in the answer area). No ink is lost.
- **Answer-side items:** 57 split-gap and 950 edge-ink flags come from mark-scheme row crops, the same layout as before; not changed by this work.
- **Visual review:** worst-case and changed items were viewed (about 40 pages, plus contact sheets of every figure block that changed by more than 60 pt). The full 440-item contact-sheet review was not repeated.
