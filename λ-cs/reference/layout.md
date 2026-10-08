# layout.md (CS): the Chemistry layout with CS names

The two CS books use the layout of `Δ-chemistry/reference/layout.md` unchanged. Only the
names differ. Code: `hub/scripts/cs/layout.py` (page engine) and
`hub/scripts/cs/build.py` (books).

| Element | P1 book | P2 book |
|---|---|---|
| File | `λ-cs/booklets/p1-topical-workbook/CS-9618-P1-Topical-Workbook.pdf` | `λ-cs/booklets/p2-topical-workbook/CS-9618-P2-Topical-Workbook.pdf` |
| Units | 1 to 8 | 9 to 12 |
| Running header (left) | "Computer Science 9618 Paper 1 Topical Workbook" | "Computer Science 9618 Paper 2 Topical Workbook" |
| Cover | "Computer Science 9618", "Paper 1 · Theory Fundamentals" | "Computer Science 9618", "Paper 2 · Fundamental Problem-solving and Programming Skills" |
| Appendix | none | the newest insert (pseudocode functions and operators), once |

Same as Chemistry: A4 portrait, margins 40/40/58/40 pt; running header (book
name, page number, "Unit n: Name" or "Unit n: Answers Section") with a thin
rule; cover of our own design; contents with one row per unit plus its
"Answers Section" row, exact page numbers (front pages reserved, filled after
the body); unit title page ("Unit n", name, item count, syllabus sections);
dark banner on the first question page of a unit and on its Answers Section;
numbered items with a bold reference (`M/J 25/P12/Q3/b`, `Q2/a,b(i,ii)`),
newest first; grey notes under the reference ("also Unit n (m marks)", "Uses
the insert (Appendix)"); vector crops of the official paper scaled to the text
width (never enlarged); Answers Section after each unit with the full-width
mark-scheme rows; Topic index; bookmarks; one PDF per unit.

CS-specific:
- A block of code (consecutive monospace lines), a table, a trace table and a
  diagram (cluster of drawings) are figures: all their bands stay on one page
  (`crops.figure_spans`). A figure taller than a page is the only case that
  can break.
- Dotted answer lines are removed. A dotted run is kept, in the picture and in
  the text layer, when it is a gap the candidate must fill inside a line of
  code or a sentence: text follows it on its line; or it ends a line of code
  whose statement is unfinished (operator, keyword or arrow before it), or
  stands in a block of code with other gaps; or it is a short run ending an
  unfinished sentence or numbered step. A run on its own, after a label
  ("Answer ......"), after a finished sentence, beside a name or a complete
  expression, or alone in a table cell is an answer line (`parse.dot_runs`).
- Page breaks: a figure moves whole to a new page when it fits on one; the
  short line before it, a line ending in a colon, a lone [mark] and an item's
  opening lines stay with what they belong to (`layout.keep_heights`,
  `layout._together`). Insert and appendix pages break between rows only.
- An item from a paper whose insert differs from the Appendix copy shows that
  paper's insert pages after its question crops, under a grey note.
- Fonts: Liberation Sans as in the Chemistry book when installed, else Noto
  Sans (this machine has Noto Sans only).
