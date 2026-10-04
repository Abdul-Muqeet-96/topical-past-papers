# layout.md — template derived from the Physics booklet

Source studied: `Ω-physics/Physics paper 2 9702 3.pdf` (scanned, 550 pages, no
text layer). Page roles were found from 14-dpi contact sheets of pages 1–40
(`scripts/thumbs.py`), then pages 5, 6 and 30 were viewed at 55 dpi.

## What the Physics booklet does
| Page role | Found at | Observed design |
|---|---|---|
| Cover | p1 | Subject title, "Paper-2", "Topical Workbook with Mark Scheme", feature bullets, editorial board, publisher block (brand — NOT copied) |
| Contents | p3 | Single page. Table: "UNIT n" cell spanning two rows; row 1 = unit name (bold) …… page; row 2 = "Answer Section" …… page |
| Blank | p4 | "BLANK PAGE" |
| Unit title page | p5, p39 | "Unit n" + unit name in large bold caps at top beside a logo box; plain sheet otherwise |
| First question page | p6 | Dark banner bar with white bold "Unit n: Name"; then numbered items |
| Question pages | p6–p29 | Running header: left "Physics A Level P-2 Topical Workbook", centre page number, right "Unit n: Name"; items numbered 1, 2, 3… with bold reference line ("M/J 23/P22/Q1"), newest first |
| Answers Section | p30–p38 | Dark banner "Answers Section" centred; running header right = "Unit n: Answers Section"; same numbering and bold references as questions |

## What this workbook does (applies the above, with CLAUDE.md rules)
- **Page**: A4 portrait (595×842 pt), margins 40 pt left/right, 50 pt top, 40 pt bottom.
- **Running header** (every page except cover/contents/unit-title pages): left
  "Chemistry 9701 Paper 2 Topical Workbook", centre page number, right
  "Unit n: Name" (or "Unit n: Answers Section"), thin rule under it.
- **Cover**: own design — no Read & Write branding. Title "Chemistry 9701",
  "Paper 2 · AS Level Structured Questions", "Part-level Topical Workbook with
  Mark Scheme", series range covered, feature bullets (newest first, each
  part filed by syllabus topic, context included, mark scheme after each unit),
  generated date.
- **Contents**: same two-row-per-unit table as the Physics booklet (unit name
  row + "Answers Section" row, page numbers right-aligned with dot leaders);
  then Topic index and Appendix rows. Two-pass build so page numbers are exact.
- **Unit title page**: "Unit n" and unit name in large bold, item count,
  syllabus section reference. No logo.
- **First question page of a unit**: dark banner with white bold "Unit n: Name".
- **Items**: number "n." + bold reference (e.g. `M/J 25/P22/Q5/b`,
  `Q3/a,b(i,ii)`), optional "also <topic> (marks split)" tag and "Data Booklet
  needed" note in small grey. Then the item's source regions (stem, context
  figures/tables, earlier parts it depends on, its own parts) merged in paper
  order with no generated labels, as in the Physics booklet.
  Crops are vector clips of the official paper scaled to fit text width (max
  scale 1.0). Items do not split across pages unless taller than a page; a figure stays
  with its label line and caption.
- **Answers Section**: dark banner "Answers Section"; same numbering and
  reference; MS row crops (full width, incl. Guidance column), plus the
  unlabelled rows of any earlier part whose answer the item uses.
- **Bookmarks**: Contents, each unit with its Answers Section, Topic index,
  Appendix (book and unit PDFs).
- **Topic index**: table reference → unit, marks, page (also in index.csv).
- **Appendix**: Periodic Table cropped once from the newest paper.
