# Physics 9702 P2 workbook: final audit and fixes

Book: `Ω-physics/booklets/p2-topical-workbook/Physics-9702-P2-Topical-Workbook.pdf`: 932 pages, 631 items
(260 from official papers with 1320 marks, 371 from the booklet). Branch `claude/physics-p2-booklet`.

## How it was checked

- **Automatic checks** (`hub/audit/physics/run_all.sh`, outputs in `hub/audit/physics/out/`):
  - `final_checks.py`: coverage, duplicates, self-containment, context, marks, references and answers.
  - pc01: book parse.
  - pc02: book, index.csv and items.jsonl agree.
  - pc03: Part B coverage and marks.
  - pc04: structure, contents and bookmarks.
  - pc05: every crop band mapped to its source page.
  - pc06: crop quality.
  - pc07: self-containment.
  - pc08: files.
- **Visual check:** all 932 pages were viewed as contact sheets. Every flagged spot was zoomed and compared with the source scan or official paper.
- **Book-wide detectors:** orphan headings, a lone mark opening a page, and captions split from their figures.

## Results (final build)

| Check | Result |
|---|---|
| Final checks (coverage, duplicates, self-containment, context, marks, refs, answers) | all 0 |
| Book / index.csv / items.jsonl | 631 / 631 / 631, 0 differences |
| Part B coverage | 708 of 708 question parts, 0 missing, 0 duplicates |
| Part B paper checks | 22 pass; 1 known: MAR 26/P22 Q5 mark-scheme codes 14 vs QP 12 (bracketed alternative marks, checked by eye, correct) |
| Self-containment of official items | 260 items, 0 issues |
| Structure, contents, bookmarks, headers | OK |
| Orphan headings / lone marks / split captions | 0 / 2 / 1 (all three are page breaks in the scanned booklet itself, kept) |

The crop heuristics in pc06 (cutfig, clipped, edgeink, sidecut, marks) flag far more than they confirm. Most of their counts come from:

- skew and noise in the scanned booklet;
- invisible clipping paths in the official PDFs.

Every new flag after each fix was looked at. All the real defects found are listed below.

## Defects found and fixed in this audit

| # | Defect | Fix | Scope |
|---|---|---|---|
| 1 | Booklet pages missing from the scan left items lost or cut short | Filled from the official paper of the same question (`hub/scripts/physics/gapfill.py`). Each paper is verified by its header, part marks = [Total] = mark-scheme marks, and a grey note is added | 7 items restored; 4 questions and 6 answers replaced; 0 failed |
| 2 | The dot-removal rule also deleted marks such as "[2]" on the next line | Removal narrowed to a thin strip through the dot centres | 11 papers (2017–19) |
| 3 | A mark at the very foot of a page was lost | Bottom filter corrected | Several items |
| 4 | Booklet heading residue at crop tops | Single whiteout strip over the heading; covers extended past band edges | Book-wide |
| 5 | Font subsetting turned × into a box | Subsetting removed from the Physics build | Book-wide |
| 6 | Booklet answer marks on the next heading's line were given to the wrong item (cut marks, half lines) | On answer pages a mark goes with the nearer text line | 21 answers |
| 7 | Marks the OCR missed on a heading line were cut at the crop bottom | Detected from ink and taken whole; the next heading is whited out | 14 items |
| 8 | Skewed first lines were cut at the crop top | Words right of the heading set the top | 19 items |
| 9 | Scan specks stretched crops over blank paper and show-through | Specks at region ends are left out | 3 regions |
| 10 | Binding-shadow blobs in the left margin | Whited out; the right margin is untouched | 2 places |
| 11 | Fill-in blanks ("……Th", equation slots, "……%" cells) were removed with answer lines | Dot runs under 60 pt are kept, in the scan and in the text layer | 27 blanks, 6 papers |
| 12 | Fraction numerator (h2 of h2/h1) was whited out at a crop top | Region top raised over first-line words | 1 place |
| 13 | A figure caption was alone on the next page | Caption bands stay with their figure | M/J 25/P22/Q3 |
| 14 | A lone "[n]" opened a page | Mark-only bands stay with the band above | 6 places |
| 15 | An answer heading was alone at a page foot | Answer headings keep room for their first block | Book-wide |
| 16 | The self-check mapped gap-filled crops to the booklet | pc05 maps them to their official QP/MS | Check fix |
| 17 | SUMMARY counted 366 booklet items (the book has 371) and called the scan gaps open | Count read from index.csv; gap text updated | Report fix |

## Kept as is

- **Errors printed in the booklet itself** (typos such as "perpendicula", a stray "V [2]"). The rule is never to retype content, so these stay.
- **Page breaks inside the scanned booklet** (a mark at the top of the next scanned page).
- **Two booklet items filed under the wrong unit by the booklet** are left out (in report.md AUTO-DECIDED).

## For the owner

The Chemistry build (`scripts/`) still subsets fonts, which broke the × sign in the Physics book. The Chemistry book was not changed (repo rule: no changes to other subjects). It is worth checking whether its × and other symbols render.
