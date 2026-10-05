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
| Tagging conventions (Paper 2 topics) | Many Paper 2 parts touch several learning outcomes at once (a module that reads a file into an array with string functions) | One rule for every part and for the blind re-tag: a part that writes or completes a module is tagged by the first that applies: text-file handling 10.3.2; array processing 10.2.3 / 10.2.4 (search, sort); stack, queue or linked list 10.4.x; otherwise procedure 11.3.1 or function 11.3.4. Trace tables / dry runs 12.3.4; flowchart from a description 9.2.7; pseudocode from a flowchart or numbered steps 9.2.6; an algorithm described in steps or structured English 9.2.5; complete algorithm from a description 9.2.4; evaluating or completing expressions with built-in functions 11.1.3, with operators only 11.1.2; a logic statement written from a problem condition 9.2.9 |
| Tagging: good programming practice | Parts asking for features that make code easier to read (meaningful names, indentation, comments) have no learning outcome of their own | Tagged 9.2.2 (use suitable identifier names), the nearest outcome; kept in the Paper 2 book |
| Tagging: Paper 2 parts on Paper 1 topics | Some Paper 2 parts test a unit 1-8 outcome: IDE debugging features (5.2.4), validation checks and check digits (6.2.2) | Tagged with that outcome and filed in the Paper 1 book (spec: a part is filed by its topic, not its paper); each is listed under "Parts filed by topic in the other paper's book". Library routines in Paper 2 stay under 11.1.3 (use built-in functions and library routines) |
| Identical variant papers | In 2021 the variant 1 and variant 3 papers have the same text: M/J 21 P11 = P13, M/J 21 P21 = P23, O/N 21 P11 = P13, O/N 21 P21 = P23 | Both papers of each pair are kept (each is a separate official paper with its own reference); their parts carry the same tags, so their items sit next to each other in a unit |
| 3 downloaded MS files | Page 1 reads title variant 'Paper 2 Problem Solving & Programming Skills' instead of the spec's wording; code, paper number, series and document type match | Accepted and logged (spec: Header check) |
| 6 downloaded MS files | Page 1 reads title variant 'Paper 2 Problem Solving & Programming' instead of the spec's wording; code, paper number, series and document type match | Accepted and logged (spec: Header check) |
| M/J 21/P22/Q1/a | topic marks tie {10: 4, 11: 4} | filed under topic 10 (topic of first sub-part) |
| M/J 26/P21/Q2/b | topic marks tie {5: 1, 12: 1} | filed under topic 5 (topic of first sub-part) |
| M/J 26/P23/Q2/d | topic marks tie {5: 1, 12: 1} | filed under topic 5 (topic of first sub-part) |

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

## Tagging

- Every lowest-level part was tagged by reading its extracted text (`scripts/cs/dump_leaves.py`), with one learning-outcome id of `λ-cs/work/syllabus.json` (unit, section, outcome). Tags: `λ-cs/work/tags_phase1.txt`, `tags_phase2.txt`.
- Unit and section names and numbers were checked against the syllabus PDF: the 12 units and 29 sections extracted by `scripts/cs/syllabus.py` are the ones the spec lists.
- Check of every unit's tags against the syllabus wording (`scripts/cs/check_tags.py`): each part's words are compared with the wording of its outcome, its notes and its section name; parts that share no significant word with their outcome, and parts whose words fit an outcome of another unit much better, are listed and read. Phase 1: 1551 parts; 16 share no word with their outcome and 189 fit another unit's wording better by vocabulary; all were read; 1 tag was changed (M/J 26/P23 Q2(b) 11.1.2 to 9.2.9, to agree with the same question in P21). The rest are vocabulary effects (a module that searches an array says "module", not "array").
- Outcomes with no Phase 1 part: 4.2.1, 6.1.2, 8.1.1, 8.3.1, 8.3.2, 8.3.3, 9.2.1, 10.4.1, 11.1.1.

## Item exclusions

| Item | Issue | Action |
|---|---|---|
| (none) | | |

## Out of syllabus (not clearly covered by the 2027-29 learning outcomes)

| Item | Issue | Action |
|---|---|---|
| (none) | | |

## Parts that need pre-release material (9608 Paper 2)

| Item | Issue | Action |
|---|---|---|
| (none) | | |

## Parts filed by topic in the other paper's book

A part is filed by its topic, not its paper (spec, Goal).

| Item | Unit | Filed in |
|---|---|---|
| M/J 23/P21/Q1/a | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| M/J 23/P22/Q5/c | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| M/J 23/P23/Q2/b | 6 Security, privacy and data integrity | Paper 2 part filed in the Paper 1 book (unit 6) |
| M/J 26/P21/Q2/b | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| M/J 26/P23/Q2/d | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| O/N 24/P22/Q1/b,c | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| O/N 25/P21/Q1/c | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| O/N 25/P21/Q6/a | 6 Security, privacy and data integrity | Paper 2 part filed in the Paper 1 book (unit 6) |

## Multi-unit lettered parts kept whole (filed under the majority unit, tagged "also")

| Item | Why not split | Marks by unit |
|---|---|---|
| M/J 21/P22/Q1/a | (a)(ii) depends on sibling ['(a)(i)'] | {'10': 4, '11': 4} |
| M/J 21/P22/Q5/a | (a)(ii) depends on sibling ['(a)(i)'] | {'10': 6, '12': 3} |
| M/J 25/P22/Q6/a | (a)(ii) depends on sibling ['(a)(i)'] | {'12': 4, '10': 3} |
| M/J 26/P21/Q2/b | (b)(ii) depends on sibling ['(b)(i)'] | {'5': 1, '12': 1} |
| M/J 26/P23/Q2/d | (d)(ii) depends on sibling ['(d)(i)'] | {'5': 1, '12': 1} |
| M/J 26/P23/Q8/a | (a)(iii) depends on sibling ['(a)(i)'] | {'10': 7, '12': 3} |
| O/N 22/P22/Q2/a | (a)(ii) depends on sibling ['(a)(i)'] | {'9': 5, '10': 2} |

## Lettered parts split by unit

25 lettered parts were split into roman-level items because their sub-parts belong to different units and each is solvable alone:

- M/J 21/P12/Q4/b: M/J 21/P12/Q4/b(i) → unit 1; M/J 21/P12/Q4/b(ii,iii) → unit 4
- M/J 23/P11/Q3/d: M/J 23/P11/Q3/d(i,ii,iii,iv,v) → unit 1; M/J 23/P11/Q3/d(vi) → unit 4
- M/J 23/P12/Q2/c: M/J 23/P12/Q2/c(i) → unit 6; M/J 23/P12/Q2/c(ii,iii) → unit 8
- M/J 23/P23/Q3/b: M/J 23/P23/Q3/b(i) → unit 10; M/J 23/P23/Q3/b(ii) → unit 9
- M/J 24/P11/Q5/c: M/J 24/P11/Q5/c(i) → unit 6; M/J 24/P11/Q5/c(ii) → unit 7
- M/J 24/P22/Q5/a: M/J 24/P22/Q5/a(i) → unit 12; M/J 24/P22/Q5/a(ii) → unit 11
- M/J 24/P23/Q6/b: M/J 24/P23/Q6/b(i) → unit 11; M/J 24/P23/Q6/b(ii) → unit 12
- M/J 24/P23/Q7/a: M/J 24/P23/Q7/a(i) → unit 12; M/J 24/P23/Q7/a(ii) → unit 11
- M/J 25/P11/Q6/a: M/J 25/P11/Q6/a(i) → unit 3; M/J 25/P11/Q6/a(ii,iii) → unit 4
- M/J 25/P21/Q7/b: M/J 25/P21/Q7/b(i) → unit 10; M/J 25/P21/Q7/b(ii) → unit 12
- M/J 25/P23/Q7/b: M/J 25/P23/Q7/b(i) → unit 10; M/J 25/P23/Q7/b(ii) → unit 11
- M/J 26/P13/Q3/c: M/J 26/P13/Q3/c(i) → unit 1; M/J 26/P13/Q3/c(ii,iii) → unit 2
- M/J 26/P21/Q2/a: M/J 26/P21/Q2/a(i) → unit 10; M/J 26/P21/Q2/a(ii,iii) → unit 9
- M/J 26/P22/Q1/a: M/J 26/P22/Q1/a(i) → unit 10; M/J 26/P22/Q1/a(ii,iii) → unit 11
- O/N 21/P11/Q4/b: O/N 21/P11/Q4/b(i) → unit 7; O/N 21/P11/Q4/b(ii) → unit 5
- O/N 21/P13/Q4/b: O/N 21/P13/Q4/b(i) → unit 7; O/N 21/P13/Q4/b(ii) → unit 5
- O/N 21/P22/Q6/c: O/N 21/P22/Q6/c(i) → unit 12; O/N 21/P22/Q6/c(ii) → unit 11
- O/N 22/P23/Q5/b: O/N 22/P23/Q5/b(i) → unit 10; O/N 22/P23/Q5/b(ii) → unit 11
- O/N 22/P23/Q7/b: O/N 22/P23/Q7/b(i) → unit 10; O/N 22/P23/Q7/b(ii) → unit 9
- O/N 23/P13/Q3/a: O/N 23/P13/Q3/a(i,ii) → unit 2; O/N 23/P13/Q3/a(iii) → unit 6
- O/N 23/P13/Q5/b: O/N 23/P13/Q5/b(i) → unit 1; O/N 23/P13/Q5/b(ii) → unit 5
- O/N 23/P22/Q6/b: O/N 23/P22/Q6/b(i,ii) → unit 11; O/N 23/P22/Q6/b(iii) → unit 10
- O/N 23/P23/Q7/b: O/N 23/P23/Q7/b(i) → unit 10; O/N 23/P23/Q7/b(ii) → unit 11
- O/N 24/P22/Q2/b: O/N 24/P22/Q2/b(i) → unit 10; O/N 24/P22/Q2/b(ii) → unit 11
- O/N 25/P12/Q8/b: O/N 25/P12/Q8/b(i) → unit 3; O/N 25/P12/Q8/b(ii) → unit 5

## Insert

| Item | Shown as | Why |
|---|---|---|
| M/J 21/P21/Q4/a,c | this paper's insert inline (1 page(s)) | uses UCASE (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| M/J 21/P21/Q4/b | this paper's insert inline (1 page(s)) | uses UCASE (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| M/J 21/P22/Q5/b | this paper's insert inline (1 page(s)) | uses LCASE (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| M/J 21/P23/Q4/a,c | this paper's insert inline (1 page(s)) | uses UCASE (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| M/J 21/P23/Q4/b | this paper's insert inline (1 page(s)) | uses UCASE (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| M/J 23/P22/Q2/a,b | this paper's insert inline (3 page(s)) | text refers to the insert; insert text differs from the Appendix |
| M/J 24/P22/Q1/b | note "Uses the insert (Appendix)" | text refers to the insert |
| M/J 24/P23/Q1/a,b | note "Uses the insert (Appendix)" | text refers to the insert |
| M/J 25/P23/Q1/a,b | note "Uses the insert (Appendix)" | text refers to the insert |
| O/N 21/P22/Q1/c,d | this paper's insert inline (3 page(s)) | text refers to the insert; insert text differs from the Appendix |
| O/N 24/P21/Q6/b | this paper's insert inline (3 page(s)) | text refers to the insert; insert text differs from the Appendix |
| O/N 24/P23/Q6 | this paper's insert inline (3 page(s)) | text refers to the insert; insert text differs from the Appendix |
| O/N 25/P21/Q1/a | note "Uses the insert (Appendix)" | text refers to the insert |

## Context added to items

Besides the stem and the lettered introduction (always shown), earlier parts were added as context for these reasons (count of context parts):

- part reference: 18
- identifier rule: 13
- scenario noun ("the ..."): 1

## Thin units (< 5 items)

- None.

## Final checks on the built books

- Coverage: every lowest-level part of every included question appears in exactly one item, or is in an exclusion list above. Unexplained gaps: 0; duplicates: 0.
- Self-containment re-check (build resolver): 0 failures; context recomputed identically for every item (0 mismatches).
- Marks re-check (item [marks] = MS marks): 0 failures.
- Every item reference found on its indexed page: 0 misses; every item has an answer entry: 0 misses.
- Every item is in the book of its unit: 0 misses.

## Layout and visual checks

- Stage 0 (test build of 7 papers): cover, contents, unit title page, P1 item pages, P2 item pages with gap-fill pseudocode, an item with its insert inline, Answers pages with "write program code" rows running over two pages, and the Appendix were rendered at 60-80 dpi and viewed. Fixed after viewing: a block of table definitions and a block of gap-fill pseudocode were split across pages (figure grouping now treats consecutive monospace lines, including lines that are only a dotted gap, as one figure); the Appendix banner now takes its reference from the insert's own header.
- Stage 4 (Phase 1 books): rendered and viewed at 62 dpi: both covers, both contents pages, P1 Answers pages (Unit 2), a P1 unit title page (Unit 4), P1 item pages with an assembly-language instruction table, the P1 Topic index, P2 item pages with a linked-list diagram, an array diagram and pseudocode (Units 10 and 11), a P2 Answers page with a program-code answer, and the P2 Appendix. Nothing needed fixing.

