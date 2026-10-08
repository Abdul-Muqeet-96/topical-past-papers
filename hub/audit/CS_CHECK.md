# CS_CHECK: self-check of the Computer Science 9618 topical workbooks

Books checked: Paper 1 book 1099 pages, Paper 2 book 1518 pages (the files in `λ-cs/booklets/p1-topical-workbook/` and `λ-cs/booklets/p2-topical-workbook/` of this commit). Written 2026-10-07 by `hub/audit/scripts/cs/c99_check_md.py` from the outputs in `hub/audit/out/cs/`.

The check scripts are in `hub/audit/scripts/cs/` and do not import the build code (`hub/scripts/cs/`): they read the raw downloads in `data/` and the finished books. `run_all.sh` runs them in order; it was run again after every rebuild.

**Result: 24 PASS, 0 FAIL, 0 NOT RUN.**

| Area | Check | Result | Counts | Script |
|---|---|---|---|---|
| Sources | Header of every downloaded file (code, paper, series, document type) | **PASS** | 546 expected files: QP 131 ok, MS 137 ok, inserts 31 ok; absent on the site: QP 50, MS 44, inserts 151; 2 files fail and both are excluded by the build and reported: 9608_w17_qp_11.pdf (unreadable), 9608_w18_ms_21.pdf (header mismatch) | `c10_sources.py` |
| Sources | 10 random files downloaded again and compared byte for byte | **PASS** | 10 of 10 identical (SHA-256) | `c11_redownload.py` |
| Paper level | Question numbers once and in order; part marks = cover total (75); printed [Total]; QP marks = MS marks per question and per part | **PASS** | 130 papers: sequence ok 130, sum = cover 130, [Total] ok 130; 4 questions with QP ≠ MS marks, all excluded by the build; 13 part-level differences, all inside excluded questions or logged label slips; differences between the audit's and the build's reading: 0; unexplained: 0 | `c20_qp_parse.py, c21_ms_parse.py, c22_compare.py (own parsers, no build code)` |
| Coverage, marks | Every lowest-level part of every verified paper is in exactly one item or in a reported exclusion; item marks = QP = MS | **PASS** | 3296 parts: 3133 in one item, 143 out of syllabus, 20 question excluded (check 3); gaps 0, in two items 0, item marks ≠ QP 0, ≠ MS 0 | `c30_book_parse.py, c31_coverage.py` |
| Consistency | Book (both sides), index.csv, items.jsonl, topics.json, unit PDFs and the build's item list agree (items, order, units, pages, marks, notes) | **PASS** | 0 findings. P1 Q headings: 663, P1 A headings: 663, P1 index rows: 663, P1 jsonl rows: 663, P1 unit PDF pages: 1086, P2 Q headings: 688, P2 A headings: 688, P2 index rows: 688, P2 jsonl rows: 688, P2 unit PDF pages: 1502 | `c40_threeway.py` |
| Consistency | Text layer: the words of every item read from the book = items.jsonl text (+ insert_text) and answer_text, within 3 % | **PASS** | 0 findings. Q items: 1351, Q tokens (jsonl): 234915, A items: 1351, A tokens (jsonl): 190913 | `c41_text.py` |
| Crop quality | Clipped text (a word box cut by a crop edge, with ink outside) | **PASS** | 0 findings | `c70_bands.py, c71_crops.py` |
| Crop quality | Marks cut or damaged ([n] at 300 dpi) | **PASS** | 0 findings. 3162 marks checked | `c71_crops.py, c72_pixels.py, c74_marks.py` |
| Crop quality | Cut figures (a drawing crossing a crop edge with visible ink beyond it) | **PASS** | 0 findings | `c71_crops.py` |
| Crop quality | Furniture: headers, footers, page numbers, barcodes, margin text, site stamps inside a crop | **PASS** | 15 flagged, all read: The crop reaches into the footer zone because a mark or the last line of a figure is printed level with the footer (12 question crops), or a mark-scheme row ends low on its page (3 answer crops). The pixel comparison finds no footer ink in any of them (furniture visible: 0) | `c71_crops.py, c72_pixels.py` |
| Crop quality | Dotted lines: answer lines still visible; gaps to fill removed | **PASS** | 0 findings. P1: 2140 answer lines removed, 192 gaps kept; P2: 1483 answer lines removed, 242 gaps kept | `c72_pixels.py` |
| Crop quality | Dropped ink: words or drawings of the shown parts missing from the book; ink removed inside a crop | **PASS** | 25 flagged, all read: Empty frames for drawing a flowchart, a structure chart or a network diagram (answer space), removed by rule (AUTO-DECIDED, empty drawing boxes). All 23 frames were viewed on their source pages, outlined: each is blank. 10125 + 12394 crops compared with their source page at 110 dpi | `c71_crops.py, c72_pixels.py` |
| Crop quality | Empty frames (answer space for a drawing) still shown | **PASS** | 0 findings | `c71_crops.py` |
| Crop quality | Added ink (in the book, not in the source), ink on a crop edge, trace of a rule lying just outside a crop | **PASS** | 0 findings | `c72_pixels.py` |
| Crop quality | Page splits: figure or code block split across pages, heading, mark or introducing line left alone, overlap, margins, empty pages, enlarged crops | **PASS** | 11 flagged, all read: Not captions cut from a figure. Each row was read: answer labels ("Register", "Bus 1", "corrected line", "Programming language"), the last line of a code listing or of a list ("OUTPUT MyString, StringTotal", "PUSH 'Y'"), a table row or table definition followed by ordinary text or by the next part ("Num[4] 3", "REPAIR_PART(...)"), and the end of a sentence ("appropriate title."); 2 flagged, all read: Both rows are the last row of a figure (a register diagram, a table definition) at the foot of a page, followed on the next page by the text of the next part; no instruction is separated from its figure | `c73_layout.py` |
| Crop quality | Pages with more than 45 % unused space that no keep-together rule explains | **PASS** | 0 findings. by rule: 209 pages: next item kept whole or its start kept together, 82 pages: figure or block kept together | `c73_layout.py` |
| Self-containment | Own parts shown; part, page, question, insert and Appendix references resolved; material announced as following is shown; identifier rule (first use of a name is in the item) | **PASS** | 3 flagged, all read: False alarms. Name (M/J 23/P12 Q2), Description (M/J 19/P11 Q2) and Temp (M/J 15/P23 Q2) are defined in the question stem, which is printed in the item; the items were read. items: 1351, "announcing lines (colon / the following ...)": 1707, part references: 109, page references: 76, Appendix references: 58, identifiers checked: 2595, "announcements (... follows)": 32, insert references: 8 | `c80_selfcontained.py` |
| Topics | Blind re-tag of every item (unit hidden), every disagreement resolved by reading the item | **PASS** | 1352 of 1352 items re-tagged: 1304 same unit, 37 filed under the second acceptable unit, 10 disagreements, 10 resolved by reading (blind/resolved.txt): all keep their tag; unresolved 0; 1 item regrouped since the blind pass (its blind unit is named in the new item's also-note) | `c90_blind_dump.py, c91_blind_compare.py` |
| Structure | Cover figures, contents, unit title pages against the syllabus, banners, running headers, page numbers, bookmarks, newest-first order, Topic index, Appendix | **PASS** | 0 failures; P1: cover None; P2: cover None | `c50_structure.py` |
| Files | Every PDF passes qpdf --check; fonts; page sizes; every file under 95 MB; csv, jsonl and json parse | **PASS** | 20 files checked, 0 failures; largest: 29648890	Δ-chemistry/booklets/p2-topical-workbook/Chemistry-9701-P2-Topical-Workbook.pdf
25899835	λ-cs/booklets/p2-topical-workbook/CS-9618-P2-Topical-Workbook.pdf
21766806	Ω-physics/reference/Physics paper 2 9702 3.pdf
; 19 fonts are not embedded in the source papers themselves and are inherited as they are | `c60_files.py` |
| Phase 2 (9608) | 9608 papers pass the same paper, coverage and crop checks; running-text mark schemes (2015-16) read by a second parser; out-of-syllabus parts reported, not in a book | **PASS** | 70 papers; mark schemes: 115 table layout, 22 running text; 143 parts out of syllabus, 0 of them in a book | `c21_ms_parse.py, c22_compare.py, c31_coverage.py` |
| Reports | Figures in SUMMARY.md and report.md against the audit's own counts (papers, items and marks per unit, pages, sizes, exclusion rows, AUTO-DECIDED rows) | **PASS** | 73 figures compared, 0 wrong | `c96_report.py` |
| Visual | At least 15 question items and 5 answers per unit viewed at 90 dpi or more | **PASS** | Final books: 180 question items and 60 answers (15 + 5 per unit, 12 units; random, seed 9625; listed in hub/audit/out/cs/visual_samples.json) rendered at 92 dpi, 120 images, all viewed: no defect found. Seven earlier rounds of the same size on earlier builds found the defects listed below, each fixed and re-checked | `c95_sheets.py sample; viewed by the model` |
| Visual | Every automated flag viewed (book crop beside its source) | **PASS** | Every row of every finding list that was not empty during the self-check was viewed as a book crop beside its source page (or read, for text findings); the lists still not empty are judged below | `cv_view.py, cv_zoom.py` |

## Findings that were read and judged

A finding list that is not empty passes only when every row was read (and viewed where it concerns a picture). `hub/audit/scripts/cs/judged.json` holds the verdicts; a verdict stops counting when the number of rows changes.

| Output file | Rows | Verdict |
|---|---|---|
| `crop_furniture.json` | 15 | The crop reaches into the footer zone because a mark or the last line of a figure is printed level with the footer (12 question crops), or a mark-scheme row ends low on its page (3 answer crops). The pixel comparison finds no footer ink in any of them (furniture visible: 0) |
| `crop_empty_box.json` | 25 | Empty frames for drawing a flowchart, a structure chart or a network diagram (answer space), removed by rule (AUTO-DECIDED, empty drawing boxes). All 23 frames were viewed on their source pages, outlined: each is blank |
| `self_identifier.json` | 3 | False alarms. Name (M/J 23/P12 Q2), Description (M/J 19/P11 Q2) and Temp (M/J 15/P23 Q2) are defined in the question stem, which is printed in the item; the items were read |
| `layout_orphan_caption.json` | 11 | Not captions cut from a figure. Each row was read: answer labels ("Register", "Bus 1", "corrected line", "Programming language"), the last line of a code listing or of a list ("OUTPUT MyString, StringTotal", "PUSH 'Y'"), a table row or table definition followed by ordinary text or by the next part ("Num[4] 3", "REPAIR_PART(...)"), and the end of a sentence ("appropriate title.") |
| `layout_orphan_lead.json` | 2 | Both rows are the last row of a figure (a register diagram, a table definition) at the foot of a page, followed on the next page by the text of the next part; no instruction is separated from its figure |

## How the checks were run

- Every script reads the raw downloads in `data/` and the finished books; none imports the build code. The question-paper and mark-scheme readers (`c20`, `c21`) are written separately from the build's readers, so a part boundary or a mark read wrongly by the build shows as a difference in `c22`.
- Every crop in the books is a Form XObject whose bounding box is the clip on the source page. `c70` reads those boxes back from the book PDFs and maps each crop to its source page; `c72` then renders every crop from the book and from the raw source page at 110 dpi and compares them pixel by pixel (best of 25 one-pixel shifts, one pixel of tolerance): ink that disappeared, ink that appeared, dotted lines, footer words, site stamps, marks.
- Dotted lines: `c72` holds its own statement of the rule that tells an answer line from a gap to fill (text before and after the run, monospace font, table borders, an arrow drawn between a name and the run) and reports an answer line that is still visible or a gap that was removed. Runs that the rule leaves to the surrounding block of code are counted, not judged.
- Layout: `c73` reads the placed crops page by page: margins, overlaps, a heading, a mark or an introducing line left alone, a figure or a code block split across pages, pages with much unused space and the reason for it.
- Topics: `c90` writes every item without its unit, section or outcome, in shuffled order; the items were tagged again from that text alone, then `c91` compares. Disagreements were resolved by reading the whole item (`hub/audit/out/cs/blind/resolved.txt`).
- The checks were repeated after every rebuild (`run_all.sh`); the figures above are from the last run, on the books of this commit.

## What the self-check found and what was changed

Found by the checks above or by viewing, and fixed in the build (each has a row in AUTO-DECIDED in `λ-cs/reports/report.md`):

- two questions (9608 M/J 18/P21 Q6, Q7) excluded although their marks are printed ("Max2", "MAX8"); two items of 9608 M/J 21/P21 Q2 lost to a mark-scheme label;
- nine papers printed at reduced scale were enlarged by 0.8 %;
- answer-line dots removed from the text layer moved other glyphs on some pages (now verified page by page, with a fallback);
- a mark on the footer line clipped by a white rectangle; barcode strips inside two items; frames of logic circuits to draw erased as empty boxes;
- running-text mark schemes (2015-16): blank tails of rows, footers inside appendix answers, a flowchart box and a fraction cut at the start of a row;
- dotted lines: labelled answer lines ("Answer ......") and answer cells of tables left visible; gaps in gap-fill pseudocode and in sentences removed; a semicolon half covered;
- the bar under a binary sum dropped; a trace of footer words or of a removed frame on the edge row of a crop;
- page breaks: code listings split, a mark, an introducing line or an opening line separated from what it belongs to;
- items.jsonl without the text of insert pages printed with an item; footer words left in the PDF text layer.
- empty frames for drawings drawn with a hairline border left in the items; the rule above the copyright paragraph of a last page cropped with the last question;
- self-containment: one introduction and three stems announcing pseudocode or a diagram that the item did not show (the part that holds it is now shown as context); one item ending with the lead-in sentence of a part that is not in the books.
