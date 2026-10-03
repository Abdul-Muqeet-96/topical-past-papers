# Report — 9701 Paper 2 part-level topical workbook

(Working log; reorganised by type in Stage 9.)

## AUTO-DECIDED
| Item | Issue | What I did |
|---|---|---|
| MS w22–w25 v21/22/23 (12 files) | Page-1 title reads "Paper 2 AS Structured Questions" (no "Level"); code, series and "MARK SCHEME" all match | Accepted as the same paper; recorded under `notes` in data/manifest.json |

## Stage log
- Stage 1: 35 Phase 1 papers (70 PDFs) downloaded; 35 pass header checks, 0 excluded.

## Stage 3 — paper-level verification (Phase 1)
- 35 papers checked; 0 papers excluded; 9 questions excluded (check 4: MS marks ≠ QP total).

| Paper | Q | Check failed | Cause (inspected) |
|---|---|---|---|
| M/J 24/P22 | Q5 | MS marks 0 != QP total 8 | MS has no rows for Q5 (MS ends at 4(e)(ii)) |
| O/N 22/P21 | Q4 | MS marks 10 != QP total 14 | MS 4(a) rows C2/D2 carry no marks (MS shows 2+2 for 8-mark part) |
| O/N 22/P23 | Q4 | MS marks 10 != QP total 14 | MS 4(a) rows C2/D2 carry no marks (MS shows 2+2 for 8-mark part) |
| O/N 23/P21 | Q4 | MS marks 15 != QP total 16 | MS row label printed as "4(a(i)" (typo), row not attributable |
| O/N 23/P23 | Q4 | MS marks 15 != QP total 16 | MS row label printed as "4(a(i)" (typo), row not attributable |
| O/N 24/P22 | Q4 | MS marks 14 != QP total 17 | MS 4(e)(i) marks cell empty |
| O/N 25/P21 | Q1 | MS marks 18 != QP total 20 | MS 1(c)(iii) "N/A": question removed from the paper by Cambridge |
| O/N 25/P22 | Q1 | MS marks 8 != QP total 10 | MS 1(c)(iii) "N/A": question removed from the paper by Cambridge |
| O/N 25/P23 | Q1 | MS marks 18 != QP total 20 | MS 1(c)(iii) "N/A": question removed from the paper by Cambridge |

## Stage 4 — part extraction (Phase 1)
- 155 included questions → 596 lettered parts, 1028 roman sub-parts; 390 Table/Fig. captions (38 without an isolable vector block; when one of those is referenced from another part, the defining part is used as context instead).
- Lettered-part default items: 595/596 self-contained after context resolution (stem + referenced Tables/Figs + earlier parts / defined labels); 67 need earlier-part context, 5 need a Table/Fig. block from another part.
- Marks check (item [marks] vs MS marks):
  | Item | Issue | Action |
  |---|---|---|
  | M/J 26/P24/Q5(e) | QP [1], MS row 5(e) = 3 marks | Excluded |
  | M/J 26/P24/Q5(f) | QP [2], MS has no 5(f) row | Excluded |
