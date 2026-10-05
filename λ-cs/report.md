# Report: Computer Science 9618 Paper 1 and Paper 2 part-level topical workbooks

All failures, exclusions and AUTO-DECIDED items, grouped by type, for both books. Nothing was retyped or patched: every question and mark-scheme crop is a vector clip of the official PDF.

## AUTO-DECIDED

| Item | Issue | What I did |
|---|---|---|
| Tooling | `pip` is not installed on this machine; PyMuPDF 1.28.2, numpy 2.5.3 and qpdf 12.4.2 are already present; Pillow is not | Nothing to install. Page renders for inspection are made with PyMuPDF only (`scripts/cs/render_pages.py`) |
| Fonts | Liberation Sans (used by the Chemistry book) is not installed | Generated text (cover, headers, references, index) uses Noto Sans; `layout.py` picks Liberation Sans when it is present |
| Downloads: series attempted | The spec lists s22, every March series and w26 as not on the site | All of them were still requested (so each is logged as unavailable): m21-m26 (variants 12, 22), s22, w26. All answer with a redirect, not a PDF |
| Downloads: w22 | O/N 2022 (9618) is on the site although the spec's list of found series does not name it | Downloaded, header-verified and included like the other series (spec: verify every paper by download) |
| Download-site watermark | The 9618 PDFs carry the site's tiled logo and a footer block (rule, site name, invisible lines ending in a trace ID) | Stripped in memory when a file is loaded (`parse.strip_watermark`); the files in data/ are left untouched |
| Paper check 2 | 9618 papers print no [Total: n] per question | The part [marks] must add up to the cover total (75); a printed [Total: n] would also be checked. A question ends where the next one starts; the last question ends just below its last [mark] |
| Reading [marks] | Bracketed numbers also occur inside questions (array elements such as `Sales[4]`, trace-table headings) | Only a `[n]` right-aligned at the right-hand margin counts as a mark |
| Dotted lines | CS papers use dots both for answer lines and for gaps inside code, sentences and table cells that the candidate must fill | Answer lines (a run at least 250 pt wide, or running to the right-hand margin on a line with little other text) are removed from the picture and the text layer. Short runs inside code, a sentence or a table cell are kept as printed |
| Mark-scheme reader | The Chemistry reader treats the word "Total" in the answer column as a total row; CS answers contain identifiers named `Total` | That rule is removed for CS (9618 mark schemes print no question totals) |
| Identifier rule | The spec asks for the part that defines an identifier to be shown with any item that uses it | Identifiers are found from the text layer: words set in the monospace font (character advance 0.6 em) that are not keywords, built-in functions or literals, plus `Name()`, CamelCase, `UPPER_SNAKE` and `File.txt` names in ordinary text. The definition site is the first part of the question, in paper order, that uses the name; an item using it gets that part as context (question crop only) |
| Scenario nouns | Papers do not number figures or tables; a later part says "the algorithm", "this flowchart", "the company" about something an earlier part introduced | When an item uses "the/this/these <noun>" for a noun that neither the stem nor the item introduces, the earlier part that first has the noun is added as context. Very general nouns (data, user, computer, program, table, file ...) are not treated this way |
| Insert: which items | Every 9618 Paper 2 prints "Refer to the insert for the list of pseudocode functions and operators" once, above Question 1; that line is not part of any item | The insert note or inline pages go to an item whose own text refers to the insert, and to an item that uses a function its own insert defines and the Appendix copy does not (LCASE, UCASE, NOW in 2021). All other items rely on the Appendix |
| Insert: text comparison | The 2024-25 inserts differ from the 2026 insert only by a colon after one "Example" and a full stop after "records" | "Matches in text" ignores punctuation at the end of a word (and white space, footers and the copyright paragraph). M/J 24, M/J 25, O/N 25 and M/J 26 inserts match the Appendix copy; 2021, 2022, 2023 and O/N 24 inserts differ |
| Appendix (P2 book) | "The insert of the newest paper": the three M/J 26 inserts have the same text | The insert of M/J 26/P23 is used (newest series, highest variant, as in the Chemistry build) |
| Figures | The spec asks that code, tables, trace tables and diagrams never split across pages; CS papers print no captions | A figure is a run of consecutive monospace lines or a cluster of drawings/images with the text inside it; all its crop bands are kept on one page. Only a figure taller than a page can break |
| Tags | The spec asks for unit, section and learning outcome per part | Learning outcomes are the "Candidates should be able to" statements of `λ-cs/cs-syllabus.pdf`, extracted by `scripts/cs/syllabus.py` and numbered in print order (1.2.3 = third outcome of section 1.2). A tag is one such id |
| items.jsonl | The book serves a student and Claude teaching the student | Besides the Chemistry fields, each line also has the sections, learning-outcome ids, answer page and the answer text from the mark scheme's text layer |
| 3 downloaded MS files | Page 1 reads title variant 'Paper 2 Problem Solving & Programming Skills' instead of the spec's wording; code, paper number, series and document type match | Accepted and logged (spec: Header check) |
| 6 downloaded MS files | Page 1 reads title variant 'Paper 2 Problem Solving & Programming' instead of the spec's wording; code, paper number, series and document type match | Accepted and logged (spec: Header check) |

## Downloads and header checks

**Phase 1 (9618)**: 84 papers attempted; 60 downloaded with QP and MS headers verified; 24 not on the site; 0 excluded for a header mismatch; 0 download failures. Inserts found: 31.

| Series | P1 papers | P2 papers | Inserts | Not on the site | Excluded |
|---|---|---|---|---|---|
| m21 | 0 | 0 | 0 | 2 | 0 |
| s21 | 3 | 3 | 3 | 0 | 0 |
| w21 | 3 | 3 | 3 | 0 | 0 |
| m22 | 0 | 0 | 0 | 2 | 0 |
| s22 | 0 | 0 | 1 | 6 | 0 |
| w22 | 3 | 3 | 3 | 0 | 0 |
| m23 | 0 | 0 | 0 | 2 | 0 |
| s23 | 3 | 3 | 3 | 0 | 0 |
| w23 | 3 | 3 | 3 | 0 | 0 |
| m24 | 0 | 0 | 0 | 2 | 0 |
| s24 | 3 | 3 | 3 | 0 | 0 |
| w24 | 3 | 3 | 3 | 0 | 0 |
| m25 | 0 | 0 | 0 | 2 | 0 |
| s25 | 3 | 3 | 3 | 0 | 0 |
| w25 | 3 | 3 | 3 | 0 | 0 |
| m26 | 0 | 0 | 0 | 2 | 0 |
| s26 | 3 | 3 | 3 | 0 | 0 |
| w26 | 0 | 0 | 0 | 6 | 0 |

Unavailable (the site answers with a redirect, no PDF): 9618_m21_12, 9618_m21_22, 9618_m22_12, 9618_m22_22, 9618_m23_12, 9618_m23_22, 9618_m24_12, 9618_m24_22, 9618_m25_12, 9618_m25_22, 9618_m26_12, 9618_m26_22, 9618_s22_11, 9618_s22_12, 9618_s22_13, 9618_s22_21, 9618_s22_22, 9618_s22_23, 9618_w26_11, 9618_w26_12, 9618_w26_13, 9618_w26_21, 9618_w26_22, 9618_w26_23.
- 9618_s22_21: only the insert is on the site (no QP or MS); not used.

## Paper-level verification failures

Checks: (1) every question number exactly once; (2) part [marks] add up to the cover total of 75; (3) MS marks of each question equal its QP marks; (4) reference from the header text.

| Paper | Scope | Failure | Action |
|---|---|---|---|
| M/J 25/P12 | Q7 | MS marks 7 != QP marks 8 | question excluded |

- Phase 1 (9618): 60 papers checked, 60 pass, 0 excluded; 1 questions excluded.

Causes (inspected):
- M/J 25/P12 Q7: the mark-scheme row 7(b)(ii) prints no value in its Marks column (source defect), so the MS marks of Q7 are 7 against 8 in the question paper. The question is excluded and nothing is patched.

