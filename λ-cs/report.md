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
| Dotted lines | CS papers use dots both for answer lines and for gaps inside code and sentences that the candidate must fill | Answer lines are removed from the picture and the text layer; gaps to fill are kept as printed. The rule that tells them apart is in the row "Gaps to fill and answer lines" below and in `parse.dot_runs` |
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
| Phase 2 downloads: series attempted | The spec lists the 9608 series found on the site | All series 2015-2021 were requested, including March (variants 12, 22), w20 and the w15/w21 variants the spec lists as missing. Not on the site: every March series, w20 (all), w15 QP 12, w21 QPs 12, 13, 21, 22, 23 (their mark schemes exist but are not used) |
| 9608 MS headers | Many 9608 mark schemes print "Paper 1 Written Paper" / "Paper 2 Written Paper" (63 files), and two print "Paper 2" with no title (M/J 17 P21, P23) | Accepted (paper number, code/variant, series and document type match); each wording is counted in the table below |
| O/N 18/P21 (9608) | The mark scheme of 9608/21 prints "Paper 1 Written Paper": wrong paper number | Paper excluded by the header rule (as Chemistry decision D5) |
| O/N 17/P11 (9608) | The question paper file on the site is damaged (truncated at 475 136 bytes; the same on a second download; PyMuPDF and qpdf cannot read it) | Paper excluded |
| References of 9608 papers in 2021 | In M/J 21 and O/N 21 both syllabuses sat papers with the same variant numbers, so "M/J 21/P11/Q3/a" would name two different parts | The seven 9608 papers of 2021 carry the code from their header in the reference: "9608 M/J 21/P11/Q3/a". All other references are unchanged |
| 9608 mark schemes 2015-2016 | They are printed as running text, not as a table ("2 (a) (i) Any one from: ... [1]") | A second reader (`parse.ms_rows_text`): a row starts at a part label at the start of a line, in the order of the question paper's own parts, and runs to the next label; marks are the [n] at the right-hand margin; "max n" is the row's mark, counted once when it is repeated under alternative solutions. Every question still has to pass check 3 and every item the [marks] = MS marks check |
| Marks not at the right-hand margin (9608) | A few 9608 papers print a mark beside a short answer line in the middle of the page, as two words ("[1" "]"), or level with the footer | Split marks are joined; a mark that ends a dotted answer line counts; a lone [n] short of the margin counts only when the paper total cannot be reached without it (M/J 17 P11 and P13: 2 marks each; M/J 17 P12: 4 marks; logged per paper). Each such paper still adds up to its cover total and every question agrees with its mark scheme |
| Line numbers of code listings (9608) | Numbered pseudocode lines at the left margin look like question numbers | A question number is never zero-padded and never set in the monospace font |
| Repeated marks on continuation rows | Some 2018 mark schemes repeat a row's label and mark on the next page | A mark repeated under the same label on a later page counts once |
| In-paper Appendix (9608 Paper 2) | 9608 Paper 2 prints the built-in functions as an "Appendix" inside the question paper (one or two pages) instead of an insert | Those pages are not question material. They are treated as the paper's insert: an item whose text refers to the Appendix shows its own paper's Appendix page(s) inline under a grey note, because that text differs from the book's Appendix (the 2026 insert) |
| "Write program code" parts (9608 Paper 2) | 9608 asks for program code in Visual Basic, Pascal or Python; the 2027-29 Paper 2 outcomes speak of pseudocode | Included and tagged by the skill tested (file handling, arrays, procedures, functions ...), as the spec's rule on "Write program code" answers implies. Where the mark scheme prints the program-code solutions in its own appendix ("Q6 (a): Visual Basic" ...), that appendix section is appended to the part's answer rows, so the answer is whole |
| Out of syllabus (Phase 2) | Topics of 9608 with no clear match in the 2027-29 outcomes | Excluded and listed: client- and server-side scripting (JavaScript, PHP, HTML), video (frame rate, interlaced/progressive encoding, spatial/temporal redundancy), features of sound- and graphics-editing software, devices not in the 3.1 list (keyboard, mouse, trackerball, scanner, inkjet printer), gateways, URL encoding characters, the three-level database schema, disk mirroring, assembler macros and directives, the named principles of the ACM/IEEE code of ethics, "transferable skills" and reading code in an unfamiliar language, numeric formatting masks, error detection and recovery as an OS task |
| Pre-release material (9608 Paper 2) | The spec excludes parts that need pre-release material | No part of the downloaded 9608 Paper 2 papers refers to pre-release material in its text; none was excluded for this reason |
| Parts whose context would exceed one page | The spec says to keep the lettered part whole or exclude; in CS the context is often a whole earlier part (a flowchart, a module table) | "About one page" is one page of the book (744 pt). A part whose context would be longer is merged with the parts it depends on into one block, filed under the unit with most marks and tagged "also" (listed under multi-unit parts kept whole). Excluded only if that is not possible |
| Small-print copyright paragraph | Some papers print the copyright paragraph at the foot of a question page | Treated as page furniture: not part of any crop or text |
| Download-site watermark (2015-2019 files) | The older 9608 files carry the site's corner ribbon and footer logo as images (added by "A-PDF Watermark" and an FPDF wrapper), sometimes over question text or a mark | The image draw operators are removed in memory at load (`parse.strip_watermark`); the text and marks underneath show again. The self-check compares every crop with its source pixel by pixel and finds no stamp left |
| Empty drawing boxes | Some questions print a large empty bordered box as space for a drawing (a flowchart, a structure chart) | An empty box is writing space and is removed like answer lines. A box with anything printed in it, or with labelled lines attached to its sides (the inputs and output of a logic circuit to draw), is a figure to complete and stays |
| References of questions without lettered parts | Some 9608 questions have roman parts directly under the question number | The reference names them in brackets: `O/N 16/P11/Q4/(i,ii)` |
| Reference line and first crop | A reference line could fall alone at the foot of a page | An item (and an answer) starts on a new page when its first crop or figure would not fit under its reference line |
| Marks printed as "Max2" / "MAX8" (M/J 18/P21) | A few rows of the 9608 M/J 18/P21 mark scheme print the mark in the Marks column as one word with "Max" | Read as the row's mark (found by the self-check: the questions had first been excluded for 'no mark printed'); Q6 and Q7 are in the books |
| Removing answer-line dots from the text layer | On 7 of 2348 question-paper pages the removal (a PDF redaction) also moved other glyphs: text set with character spacing, e.g. a mark shown as "[1 ]" | Every page is compared before and after, character by character. A page on which anything but the dots changed is used unchanged: its answer lines are hidden by white rectangles instead and stay in the PDF text layer (not in items.jsonl). The pages are listed below per paper |
| Gaps to fill and answer lines | A dotted run can be an answer line ("Answer ......", "Line number: ......", a line of dots on its own) or a gap inside code or a sentence ("DECLARE ...... : STRING", "PC ← ...... + 1", "The values ... will indicate ......") | Kept as a gap: a run followed by text on its line (any length); a run that ends a line of code whose statement is visibly unfinished (it stops at an operator, a keyword or an assignment arrow: "WHILE ......", "NextChar ← ......"), or that stands in a block of code with other gaps; a short run (under 250 pt) that ends an unfinished sentence or numbered step. Removed as an answer line: a run on its own; a run after a label ("Answer", "Hours worked", "Logic gate:"), after a finished sentence, or beside a name or a complete expression ("ItemStatus ......", "CONCAT(\"Studio\", 54) ......"); a run whose neighbouring text is in another cell of a table (a border lies between them). Code is recognised by its monospace font; an arrow that is a drawing is found by its ink |
| Mark printed on the footer line | The last mark of a page is sometimes printed level with "[Turn over" or the paper code | The mark is kept; the footer words beside or under it are covered by white rectangles that start below the mark's own ink |
| Papers printed at reduced scale | Nine 9608 question papers (M/J 21 P12-P23, O/N 19 P11-P22) are printed at 95.2 % of the standard size | Their pages are re-scaled to standard size before any coordinate rule is applied; the scale is measured from the footer "©" (x = 49.61 pt on a standard paper). Crops are never enlarged beyond the standard size |
| Barcode strips inside the type area | M/J 24 P13 and P23 print a barcode strip below the page number, at the height where other papers start their text | Treated as page furniture (thin glyph rows without letters or digits above y = 73 pt) |
| Running-text mark schemes: blank tails | A row of a 2015-16 mark scheme, and an appended program-code appendix section, runs to the foot of its page | Each such segment is cut back to its ink, so no blank strip goes into the Answers Sections; the footer line of a mark-scheme page is never part of a segment |
| Part that refers forward (O/N 15 P21/P23 Q5(a)) | Part (a) says "Study the incomplete pseudocode which follows in part (b)"; (a) and (b) are filed under different units | The later part is shown with the item as context (question crop only). A reference to a later part counts as a dependency only when the text sends the reader there for material ("which follows in part", "shown/given/described in part") |
| Malformed stream in a source font | One compressed stream of a font carried over from the source papers does not end properly; viewers read it, `qpdf --check` warns | The stream is stored again from its decoded bytes when a book or unit PDF is saved; its content is unchanged |
| Running-text mark schemes: where a row starts | In four 2015 mark schemes (O/N 15 P11, P13: 8(b)(i); O/N 15 P21, P23: 4) a fraction or the frame of a flowchart box starts a few points above the line of the part label | The cut between the two rows is moved up to the nearest blank strip (at most 15 pt), so the drawing stays whole and with its own row |
| Hairline under a line of text | The bar under a binary addition (O/N 22/P12 Q2(b)) is a hairline too faint to count as ink, so it fell into the removed blank space | A thin rule drawn up to 4.5 pt under a line of text and no wider than that line is kept with it |
| Footer words under a figure | Where a figure or a mark reaches down to the footer line, the footer words beside it are covered by white rectangles; at the last pixel row of the crop a faint trace of them could remain | A white rectangle that runs past the foot of a crop is drawn 0.6 pt beyond it (over blank paper) |
| Page breaks: what stays together | A figure can only be kept whole if the lines before it leave room; a mark printed after removed answer space, or the line that introduces a figure, could be left alone on the other side of a page break | A figure (code block, table, diagram) moves to a new page whole whenever it fits on one; the one to three lines printed last before it (at most 60 pt of blank answer space between them) moves with it; a line that ends with a colon ("... after execution of the instruction:") stays with what it introduces (also where the paper itself turns the page after the colon); the one to three opening lines of an item that lead straight into a figure stay with it and with the item's reference line; a caption or title of one to three words ("Stack") stays with what is printed directly under it; a band that holds nothing but a [mark] stays with the line before it. Only a figure taller than a page breaks |
| Code blocks with single-letter names | A line such as "n ← 0" has no monospace word of two letters and was not counted as code, so a listing with such lines fell apart into several figures and could break across pages | A line whose characters are monospace continues the block of code directly above it |
| Insert and appendix pages: page breaks | The pages of an insert (or of a 9608 appendix) printed with an item, and the Appendix of the Paper 2 book, are longer than a page as a whole | They may break between rows or boxes of the function tables, never inside one; a heading stays with the first row under it |
| items.jsonl: insert pages | An item that shows its paper's own insert or appendix pages has that reference material in the book but not in the "text" field | A field "insert_text" carries the text of those pages (null for every other item), so the item can be read from items.jsonl alone |
| Footer words in the text layer | On 247 question-paper pages a mark or a figure reaches down to the footer line, so "[Turn over" or the barcode glyphs fall inside a crop: hidden by white rectangles, but still in the PDF text layer | On those pages the footer words are removed from the text layer together with the answer-line dots, under the same before-and-after comparison. On 13 pages the comparison fails with the footer words included; there only the dots are removed and the footer words stay in the text layer under their white rectangle (never in items.jsonl) |
| Material announced in an introduction | 9608 M/J 15/P23 Q4(b): the introduction says "Incomplete pseudocode follows", but the pseudocode is printed inside sub-part (b)(i); item Q4/b(ii), filed in the Paper 1 book, showed the introduction without it | Where a lettered introduction announces pseudocode, program code, an algorithm or a flowchart that "follows" and the first sub-part holds it, every other sub-part of that letter depends on the first one. One part is affected: 9608 M/J 15/P23 Q4(b). Its sub-part (b)(ii) (2 marks, Unit 6) can no longer be filed apart from (b)(i), so (b) is kept whole under the rule for parts that depend on a sibling: item M/J 15/P23/Q4/b,c in the Paper 2 book, Unit 10, with the note "also Unit 6 (2 marks)". The books now hold 1351 items (Paper 1 book 663, Paper 2 book 688) |
| Rule above the copyright paragraph | The last page of a question paper prints a rule across the page above the small-print copyright paragraph; where the last question ends on that page, the rule was cropped with it | The rule (up to 16 pt above the paragraph) is treated as part of the paragraph and left out |
| Empty drawing boxes: hairline frames | Twelve empty frames for drawing a flowchart, a structure chart or a network diagram are drawn with a hairline that renders lighter than ordinary ink, so they were not recognised as empty boxes and stayed in the items | A frame counts as drawn when any trace of its border is there; all 28 empty frames are now removed like other answer space. Frames with labelled inputs and outputs on their sides (logic circuits to draw) stay |
| Lead-in of a part that is not shown | 9608 M/J 21/P12 Q5: a sentence that introduces part (f) is printed at the top of the next page, after the mark of part (e)(ii); item Q5/e(ii) ended with that sentence although (f) is not in the books | One to three lines of plain text printed at the top of a later page, after a part's last mark and directly above the label of the next part, are left out of an item that does not show that next part. One item is affected |
| Material announced in the stem | 9608 M/J 17 P11 Q4, P12 Q5 and P13 Q4: the stem ends "The following diagram shows the contents of a section of main memory and the Index Register (IX)." and the diagram is printed beside part (a); the items for the hexadecimal sub-part (P11 Q4/d(i), P12 Q5/c(i), P13 Q4/d(i)) showed the sentence without the diagram | Where the last sentence of a stem announces "the following" diagram, table, pseudocode, program code, algorithm or flowchart and the first part holds it, an item that does not contain that part shows it as context (question crop only). Three items are affected; each now shows part (a) |
| 2 downloaded MS files | Page 1 reads title missing: 'Paper 2' only instead of the spec's wording; code, paper number, series and document type match | Accepted and logged (spec: Header check) |
| 6 downloaded MS files | Page 1 reads title variant 'Paper 1 (Written Paper)' instead of the spec's wording; code, paper number, series and document type match | Accepted and logged (spec: Header check) |
| 27 downloaded MS files | Page 1 reads title variant 'Paper 1 Written Paper' instead of the spec's wording; code, paper number, series and document type match | Accepted and logged (spec: Header check) |
| 6 downloaded MS files | Page 1 reads title variant 'Paper 2 (Written Paper)' instead of the spec's wording; code, paper number, series and document type match | Accepted and logged (spec: Header check) |
| 3 downloaded MS files | Page 1 reads title variant 'Paper 2 Problem Solving & Programming Skills' instead of the spec's wording; code, paper number, series and document type match | Accepted and logged (spec: Header check) |
| 6 downloaded MS files | Page 1 reads title variant 'Paper 2 Problem Solving & Programming' instead of the spec's wording; code, paper number, series and document type match | Accepted and logged (spec: Header check) |
| 24 downloaded MS files | Page 1 reads title variant 'Paper 2 Written Paper' instead of the spec's wording; code, paper number, series and document type match | Accepted and logged (spec: Header check) |
| M/J 15/P21 QP page(s) 14 | Removing the answer-line dots from the text layer moved other glyphs on the page (text set with character spacing) | Page used unchanged: its dotted lines are hidden by white-outs and stay in the PDF text layer (not in items.jsonl) |
| M/J 15/P22 QP page(s) 14 | Removing the answer-line dots from the text layer moved other glyphs on the page (text set with character spacing) | Page used unchanged: its dotted lines are hidden by white-outs and stay in the PDF text layer (not in items.jsonl) |
| M/J 20/P12 QP page(s) 13 | Removing the answer-line dots from the text layer moved other glyphs on the page (text set with character spacing) | Page used unchanged: its dotted lines are hidden by white-outs and stay in the PDF text layer (not in items.jsonl) |
| M/J 20/P21 MS label "5(a)(i)" | The question paper has no sub-parts in 5(a) | The row is the answer of 5(a) (unambiguous) |
| 9608 M/J 21/P21 MS label "2" | Typo in the mark scheme | Read as 2(a) (unambiguous) |
| O/N 15/P21 QP page(s) 14, 17 | Removing the answer-line dots from the text layer moved other glyphs on the page (text set with character spacing) | Page used unchanged: its dotted lines are hidden by white-outs and stay in the PDF text layer (not in items.jsonl) |
| O/N 15/P22 QP page(s) 2, 13, 15 | Removing the answer-line dots from the text layer moved other glyphs on the page (text set with character spacing) | Page used unchanged: its dotted lines are hidden by white-outs and stay in the PDF text layer (not in items.jsonl) |
| O/N 15/P23 QP page(s) 14, 17 | Removing the answer-line dots from the text layer moved other glyphs on the page (text set with character spacing) | Page used unchanged: its dotted lines are hidden by white-outs and stay in the PDF text layer (not in items.jsonl) |
| O/N 16/P11 MS label "5" | Typo in the mark scheme | Read as 5(i) (unambiguous) |
| O/N 16/P13 MS label "5" | Typo in the mark scheme | Read as 5(i) (unambiguous) |
| O/N 16/P21 QP page(s) 8, 18 | Removing the answer-line dots from the text layer moved other glyphs on the page (text set with character spacing) | Page used unchanged: its dotted lines are hidden by white-outs and stay in the PDF text layer (not in items.jsonl) |
| O/N 16/P22 QP page(s) 6, 17 | Removing the answer-line dots from the text layer moved other glyphs on the page (text set with character spacing) | Page used unchanged: its dotted lines are hidden by white-outs and stay in the PDF text layer (not in items.jsonl) |
| O/N 16/P23 QP page(s) 8, 18 | Removing the answer-line dots from the text layer moved other glyphs on the page (text set with character spacing) | Page used unchanged: its dotted lines are hidden by white-outs and stay in the PDF text layer (not in items.jsonl) |
| O/N 18/P22 MS label "1(a)(i)" | The question paper has no sub-parts in 1(a) | The row is the answer of 1(a) (unambiguous) |
| O/N 18/P23 MS label "1(a)(i)" | The question paper has no sub-parts in 1(a) | The row is the answer of 1(a) (unambiguous) |
| O/N 19/P13 MS label "3c" | Typo in the mark scheme | Read as 3(c) (unambiguous) |
| M/J 21/P22/Q1/a | topic marks tie {10: 4, 11: 4} | filed under topic 10 (topic of first sub-part) |
| M/J 26/P21/Q2/b | topic marks tie {5: 1, 12: 1} | filed under topic 5 (topic of first sub-part) |
| M/J 26/P23/Q2/d | topic marks tie {5: 1, 12: 1} | filed under topic 5 (topic of first sub-part) |
| M/J 18/P21/Q1/b | topic marks tie {11: 5, 10: 5} | filed under topic 11 (topic of first sub-part) |
| M/J 18/P22/Q1/b | topic marks tie {11: 5, 10: 5} | filed under topic 11 (topic of first sub-part) |
| M/J 18/P23/Q1/b | topic marks tie {11: 5, 10: 5} | filed under topic 11 (topic of first sub-part) |
| M/J 19/P23/Q1/b | topic marks tie {11: 5, 10: 5} | filed under topic 11 (topic of first sub-part) |
| M/J 20/P21/Q2/b | topic marks tie {12: 4, 11: 4} | filed under topic 12 (topic of first sub-part) |
| 9608 M/J 21/P23/Q1/b | topic marks tie {11: 2, 10: 2} | filed under topic 11 (topic of first sub-part) |
| O/N 15/P21/Q8/c,d | same-unit parts could not be merged into one item | kept as separate items |
| O/N 15/P23/Q8/c,d | same-unit parts could not be merged into one item | kept as separate items |
| O/N 18/P22/Q1/b | topic marks tie {10: 5, 11: 5} | filed under topic 10 (topic of first sub-part) |
| O/N 18/P23/Q1/b | topic marks tie {10: 5, 11: 5} | filed under topic 10 (topic of first sub-part) |

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

**Phase 2 (9608)**: 98 papers attempted; 70 downloaded with QP and MS headers verified; 26 not on the site; 2 excluded for a header mismatch; 0 download failures. Inserts found: 0.

| Series | P1 papers | P2 papers | Inserts | Not on the site | Excluded |
|---|---|---|---|---|---|
| m15 | 0 | 0 | 0 | 2 | 0 |
| s15 | 3 | 3 | 0 | 0 | 0 |
| w15 | 2 | 3 | 0 | 1 | 0 |
| m16 | 0 | 0 | 0 | 2 | 0 |
| s16 | 3 | 3 | 0 | 0 | 0 |
| w16 | 3 | 3 | 0 | 0 | 0 |
| m17 | 0 | 0 | 0 | 2 | 0 |
| s17 | 3 | 3 | 0 | 0 | 0 |
| w17 | 2 | 3 | 0 | 0 | 1 |
| m18 | 0 | 0 | 0 | 2 | 0 |
| s18 | 3 | 3 | 0 | 0 | 0 |
| w18 | 3 | 2 | 0 | 0 | 1 |
| m19 | 0 | 0 | 0 | 2 | 0 |
| s19 | 3 | 3 | 0 | 0 | 0 |
| w19 | 3 | 3 | 0 | 0 | 0 |
| m20 | 0 | 0 | 0 | 2 | 0 |
| s20 | 3 | 3 | 0 | 0 | 0 |
| w20 | 0 | 0 | 0 | 6 | 0 |
| m21 | 0 | 0 | 0 | 2 | 0 |
| s21 | 3 | 3 | 0 | 0 | 0 |
| w21 | 1 | 0 | 0 | 5 | 0 |

Unavailable (the site answers with a redirect, no PDF): 9608_m15_12, 9608_m15_22, 9608_m16_12, 9608_m16_22, 9608_m17_12, 9608_m17_22, 9608_m18_12, 9608_m18_22, 9608_m19_12, 9608_m19_22, 9608_m20_12, 9608_m20_22, 9608_m21_12, 9608_m21_22, 9608_w15_12, 9608_w20_11, 9608_w20_12, 9608_w20_13, 9608_w20_21, 9608_w20_22, 9608_w20_23, 9608_w21_12, 9608_w21_13, 9608_w21_21, 9608_w21_22, 9608_w21_23.
- 9608_w17_11 excluded: qp: unreadable: RuntimeError('code=7: Invalid number of pages')
- 9608_w18_21 excluded: ms: paper title not on page 1

## Paper-level verification failures

Checks: (1) every question number exactly once; (2) part [marks] add up to the cover total of 75; (3) MS marks of each question equal its QP marks; (4) reference from the header text.

| Paper | Scope | Failure | Action |
|---|---|---|---|
| M/J 25/P12 | Q7 | MS marks 7 != QP marks 8 | question excluded |
| M/J 15/P23 | Q1 | MS marks 7 != QP marks 9 | question excluded |
| O/N 17/P21 | Q1 | MS marks 18 != QP marks 17 | question excluded |
| O/N 17/P23 | Q1 | MS marks 18 != QP marks 17 | question excluded |

- Phase 1 (9618): 60 papers checked, 60 pass, 0 excluded; 1 questions excluded.
- Phase 2 (9608): 70 papers checked, 70 pass, 0 excluded; 3 questions excluded.

Causes (inspected, and confirmed by the self-check's independent readers `audit/scripts/cs/c20_qp_parse.py`, `c21_ms_parse.py`, `c22_compare.py`):
- M/J 25/P12 Q7 (9618): the mark-scheme row 7(b)(ii) prints no value in its Marks column (source defect), so the MS marks of Q7 are 7 against 8 in the question paper.
- M/J 15/P23 Q1 (9608): the running-text mark scheme prints 7 marks for the question against 9 in the question paper (part (a) carries one [1] for a 3-mark part).
- O/N 17/P21 and P23 Q1 (9608, identical papers): the mark scheme prints 2 for part 1(a)(ii), the question paper [1].
Nothing is patched: each of these questions is excluded.

Found and corrected by the self-check: M/J 18/P21 Q6 and Q7 (9608) had first been excluded because rows 6(a)(i), 6(b) and 7 seemed to print no mark; their Marks column reads "Max2", "MAX8" and "Max7" (one word). The reader now takes these as marks and both questions are in the books. 9608 M/J 21/P21 Q2 had lost both its items because its first mark-scheme row is labelled "2" instead of "2(a)"; the row is now read as 2(a) (the only part without a row, equal marks; logged above as a label fix).

## Tagging

- Every lowest-level part was tagged by reading its extracted text (`scripts/cs/dump_leaves.py`), with one learning-outcome id of `λ-cs/work/syllabus.json` (unit, section, outcome). Tags: `λ-cs/work/tags_phase1.txt`, `tags_phase2.txt`.
- Unit and section names and numbers were checked against the syllabus PDF: the 12 units and 29 sections extracted by `scripts/cs/syllabus.py` are the ones the spec lists.
- Check of every unit's tags against the syllabus wording (`scripts/cs/check_tags.py`): each part's words are compared with the wording of its outcome, its notes and its section name; parts that share no significant word with their outcome, and parts whose words fit an outcome of another unit much better, are listed and read. Phase 1: 1551 parts; 16 share no word with their outcome and 189 fit another unit's wording better by vocabulary; all were read; 1 tag was changed (M/J 26/P23 Q2(b) 11.1.2 to 9.2.9, to agree with the same question in P21). The rest are vocabulary effects (a module that searches an array says "module", not "array").
- Outcomes with no Phase 1 part: 4.2.1, 6.1.2, 8.1.1, 8.3.1, 8.3.2, 8.3.3, 9.2.1, 10.4.1, 11.1.1.
- Phase 2 (9608), same check: 1725 parts (1582 tagged with an outcome, 143 marked out of syllabus); 26 parts share no word with their outcome and 203 fit another unit's wording better by vocabulary; all were read and no tag was changed. Most of the 26 are "write program code" parts filed under a pseudocode outcome (the 2027-29 outcomes speak of pseudocode only). Outcomes with no Phase 2 part: 31 (the list is printed by `check_tags.py phase2`).
- Blind re-tag (self-check, `audit/scripts/cs/c90_blind_dump.py`, `c91_blind_compare.py`): every one of the 1352 items was read again without its unit, section or outcome (shuffled, own parts only, text taken from the raw question papers with the audit's own part boundaries) and given a unit, plus a second acceptable unit where the parts legitimately span two. Result (1352 items at the time of the blind pass): 1305 items the same unit, 37 filed under the second acceptable unit, 10 disagreements. One of the 1305, M/J 15/P23/Q4/b(ii) (blind: Unit 6), was later joined to its sibling parts as item M/J 15/P23/Q4/b,c (Unit 10, note "also Unit 6"); `c91_blind_compare.py` follows each blind tag to the item that holds its parts today. The 10 were resolved by reading the whole item (`audit/out/cs/blind/resolved.txt`): all 10 keep their tag (7 are the readability / good-practice parts filed under 9.2.2 by the convention in AUTO-DECIDED; the others are an algorithm amendment under 12.3.8, a bubble-sort recognition under 10.2.4 and a string-checking function under 11.3.4).
- Tags added during the self-check: 9608 M/J 18/P21 Q6 (a)(i), (a)(ii) = 10.2.1, (b) = 10.2.3 and Q7 = 11.3.4 (the two questions that came back after the mark-scheme reader was fixed), by reading their text, consistent with the sibling paper M/J 18/P23.

## Item exclusions

| Item | Issue | Action |
|---|---|---|
| (none) | | |

## Out of syllabus (not clearly covered by the 2027-29 learning outcomes)

| Item | Issue | Action |
|---|---|---|
| M/J 15/P11/Q2/b | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 15/P11/Q5/a | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 15/P11/Q5/c(ii) | no clear match in the 2027-29 learning outcomes | excluded (rest of the lettered part kept) |
| M/J 15/P11/Q6/a | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 15/P12/Q2/b | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 15/P12/Q5/a | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 15/P12/Q5/c(ii) | no clear match in the 2027-29 learning outcomes | excluded (rest of the lettered part kept) |
| M/J 15/P12/Q6/a | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 16/P11/Q6 | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 16/P12/Q6 | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 17/P11/Q2/a(ii) | no clear match in the 2027-29 learning outcomes | excluded (rest of the lettered part kept) |
| M/J 17/P11/Q7/a | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 17/P11/Q7/b | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 17/P11/Q7/c(i,ii,iii,iv) | no clear match in the 2027-29 learning outcomes | excluded (rest of the lettered part kept) |
| M/J 17/P12/Q2/a | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 17/P12/Q2/b | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 17/P12/Q6/c(i,ii,iii,iv) | no clear match in the 2027-29 learning outcomes | excluded (rest of the lettered part kept) |
| M/J 17/P13/Q2/a(ii) | no clear match in the 2027-29 learning outcomes | excluded (rest of the lettered part kept) |
| M/J 17/P13/Q7/a | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 17/P13/Q7/b | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 17/P13/Q7/c(i,ii,iii,iv) | no clear match in the 2027-29 learning outcomes | excluded (rest of the lettered part kept) |
| M/J 18/P11/Q5/c | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 18/P12/Q5/d | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 18/P12/Q6/a | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 18/P12/Q6/b | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 18/P12/Q6/c | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 18/P12/Q6/d | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 18/P13/Q1/a | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 18/P13/Q1/b | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 18/P13/Q1/c | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 18/P13/Q1/d | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 18/P13/Q6/e | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 19/P11/Q2/b(ii) | no clear match in the 2027-29 learning outcomes | excluded (rest of the lettered part kept) |
| M/J 19/P11/Q4/a | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 19/P11/Q4/b | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 19/P11/Q6/a | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 19/P11/Q6/b | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 19/P11/Q6/c | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 19/P12/Q1/c | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 19/P12/Q4/b | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 19/P13/Q5/b | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 19/P21/Q2/b | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 19/P21/Q2/c | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 19/P22/Q2/c | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 19/P23/Q3/b | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 20/P11/Q3/a | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 20/P11/Q3/b | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 20/P11/Q3/c | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 20/P11/Q8/c | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 20/P12/Q7/c | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 20/P13/Q7/a | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 20/P13/Q7/e | no clear match in the 2027-29 learning outcomes | excluded |
| M/J 20/P22/Q1/b | no clear match in the 2027-29 learning outcomes | excluded |
| 9608 M/J 21/P11/Q6/a | no clear match in the 2027-29 learning outcomes | excluded |
| 9608 M/J 21/P11/Q6/b | no clear match in the 2027-29 learning outcomes | excluded |
| 9608 M/J 21/P11/Q6/c | no clear match in the 2027-29 learning outcomes | excluded |
| 9608 M/J 21/P11/Q6/d | no clear match in the 2027-29 learning outcomes | excluded |
| 9608 M/J 21/P11/Q6/e | no clear match in the 2027-29 learning outcomes | excluded |
| 9608 M/J 21/P12/Q5/a | no clear match in the 2027-29 learning outcomes | excluded |
| 9608 M/J 21/P12/Q5/b | no clear match in the 2027-29 learning outcomes | excluded |
| 9608 M/J 21/P12/Q5/c | no clear match in the 2027-29 learning outcomes | excluded |
| 9608 M/J 21/P12/Q5/d | no clear match in the 2027-29 learning outcomes | excluded |
| 9608 M/J 21/P12/Q5/e(i) | no clear match in the 2027-29 learning outcomes | excluded (rest of the lettered part kept) |
| 9608 M/J 21/P12/Q5/f | no clear match in the 2027-29 learning outcomes | excluded |
| 9608 M/J 21/P13/Q4/a(ii) | no clear match in the 2027-29 learning outcomes | excluded (rest of the lettered part kept) |
| 9608 M/J 21/P13/Q5/a | no clear match in the 2027-29 learning outcomes | excluded |
| 9608 M/J 21/P13/Q5/b | no clear match in the 2027-29 learning outcomes | excluded |
| 9608 M/J 21/P13/Q5/c | no clear match in the 2027-29 learning outcomes | excluded |
| 9608 M/J 21/P13/Q6/a | no clear match in the 2027-29 learning outcomes | excluded |
| 9608 M/J 21/P13/Q9/b | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 15/P11/Q3/b(ii) | no clear match in the 2027-29 learning outcomes | excluded (rest of the lettered part kept) |
| O/N 15/P11/Q7/c | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 15/P13/Q3/b(ii) | no clear match in the 2027-29 learning outcomes | excluded (rest of the lettered part kept) |
| O/N 15/P13/Q7/c | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 16/P11/Q4/(i) | no clear match in the 2027-29 learning outcomes | excluded (rest of the lettered part kept) |
| O/N 16/P11/Q4/(iii,iv) | no clear match in the 2027-29 learning outcomes | excluded (rest of the lettered part kept) |
| O/N 16/P12/Q2/a | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 16/P12/Q2/b | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 16/P12/Q2/c | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 16/P13/Q4/(i) | no clear match in the 2027-29 learning outcomes | excluded (rest of the lettered part kept) |
| O/N 16/P13/Q4/(iii,iv) | no clear match in the 2027-29 learning outcomes | excluded (rest of the lettered part kept) |
| O/N 16/P22/Q3/a | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 16/P22/Q3/b | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 17/P12/Q4/c | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 17/P12/Q5/b | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 17/P12/Q6/a | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 17/P13/Q6/b | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 17/P21/Q4/a | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 17/P21/Q4/b | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 17/P22/Q1/a(iii) | no clear match in the 2027-29 learning outcomes | excluded (rest of the lettered part kept) |
| O/N 17/P22/Q1/b(ii) | no clear match in the 2027-29 learning outcomes | excluded (rest of the lettered part kept) |
| O/N 17/P23/Q4/a | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 17/P23/Q4/b | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 18/P11/Q1/c | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 18/P11/Q1/d | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 18/P11/Q1/e | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 18/P11/Q6/a | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 18/P11/Q6/b | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 18/P11/Q6/c | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 18/P11/Q6/d | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 18/P22/Q3/a | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 19/P11/Q2/a(iv) | no clear match in the 2027-29 learning outcomes | excluded (rest of the lettered part kept) |
| O/N 19/P11/Q4/b | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 19/P12/Q3/a | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 19/P12/Q3/b | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 19/P12/Q3/c | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 19/P12/Q3/d | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 19/P12/Q5/a | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 19/P12/Q6/d(ii) | no clear match in the 2027-29 learning outcomes | excluded (rest of the lettered part kept) |
| O/N 19/P12/Q6/e(iii) | no clear match in the 2027-29 learning outcomes | excluded (rest of the lettered part kept) |
| O/N 19/P13/Q2/b(iii) | no clear match in the 2027-29 learning outcomes | excluded (rest of the lettered part kept) |
| O/N 19/P13/Q6/a | no clear match in the 2027-29 learning outcomes | excluded |
| O/N 19/P23/Q2/b | no clear match in the 2027-29 learning outcomes | excluded |
| 9608 O/N 21/P11/Q2/b | no clear match in the 2027-29 learning outcomes | excluded |
| 9608 O/N 21/P11/Q3 | no clear match in the 2027-29 learning outcomes | excluded |
| 9608 O/N 21/P11/Q4/b | no clear match in the 2027-29 learning outcomes | excluded |

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
| M/J 18/P21/Q5/b | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| M/J 18/P22/Q5/b | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| M/J 18/P23/Q5/b | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| M/J 19/P22/Q2/b | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| M/J 19/P23/Q2/d | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| M/J 20/P22/Q1/d | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| M/J 20/P23/Q1/d | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| M/J 20/P23/Q5/d(iii) | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| 9608 M/J 21/P21/Q1/a | 1 Information representation | Paper 2 part filed in the Paper 1 book (unit 1) |
| 9608 M/J 21/P21/Q4/b | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| 9608 M/J 21/P21/Q5/a(ii) | 6 Security, privacy and data integrity | Paper 2 part filed in the Paper 1 book (unit 6) |
| 9608 M/J 21/P21/Q5/b(iii) | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| 9608 M/J 21/P22/Q1/b | 1 Information representation | Paper 2 part filed in the Paper 1 book (unit 1) |
| 9608 M/J 21/P22/Q5/a | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| O/N 15/P21/Q2 | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| O/N 15/P21/Q7/c | 6 Security, privacy and data integrity | Paper 2 part filed in the Paper 1 book (unit 6) |
| O/N 15/P23/Q2 | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| O/N 15/P23/Q7/c | 6 Security, privacy and data integrity | Paper 2 part filed in the Paper 1 book (unit 6) |
| O/N 16/P21/Q4/a,b | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| O/N 16/P23/Q4/a,b | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| O/N 17/P22/Q1/b(i) | 1 Information representation | Paper 2 part filed in the Paper 1 book (unit 1) |
| O/N 17/P22/Q4/b | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| O/N 19/P21/Q2/b | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| O/N 19/P22/Q2/b | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |
| O/N 19/P23/Q2/c | 5 System Software | Paper 2 part filed in the Paper 1 book (unit 5) |

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
| M/J 15/P21/Q5/e | context for ['(e)(i)'] exceeds one page | {'9': 3, '10': 7} |
| M/J 15/P22/Q5/e | context for ['(e)(i)'] exceeds one page | {'9': 3, '10': 7} |
| M/J 15/P23/Q4/b | (b)(ii) depends on sibling ['(b)(i)'] | {'10': 8, '6': 2} |
| M/J 16/P21/Q1/a | (a)(ii) depends on sibling ['(a)(i)'] | {'9': 6, '11': 8} |
| M/J 16/P22/Q1/a | (a)(ii) depends on sibling ['(a)(i)'] | {'9': 6, '11': 8} |
| M/J 16/P23/Q1/a | (a)(ii) depends on sibling ['(a)(i)'] | {'9': 6, '11': 8} |
| M/J 18/P21/Q1/b | (b)(ii) depends on sibling ['(b)(i)'] | {'11': 5, '10': 5} |
| M/J 18/P22/Q1/b | (b)(ii) depends on sibling ['(b)(i)'] | {'11': 5, '10': 5} |
| M/J 18/P23/Q1/b | (b)(ii) depends on sibling ['(b)(i)'] | {'11': 5, '10': 5} |
| M/J 19/P23/Q1/b | (b)(ii) depends on sibling ['(b)(i)'] | {'11': 5, '10': 5} |
| M/J 20/P21/Q2/b | context for ['(b)(i)', '(b)(ii)'] exceeds one page | {'12': 4, '11': 4} |
| 9608 M/J 21/P21/Q3/b | context for ['(b)(i)'] exceeds one page | {'11': 2, '12': 3} |
| 9608 M/J 21/P23/Q1/b | (b)(ii) depends on sibling ['(b)(i)'] | {'11': 2, '10': 2} |
| O/N 15/P21/Q6/c | context for ['(c)(i)', '(c)(ii)', '(c)(iii)'] exceeds one page | {'11': 5, '10': 2} |
| O/N 15/P21/Q8/a,b,c | context of O/N 15/P21/Q8/c would exceed one page (968 pt): kept with the parts it depends on | {'11': 4, '12': 7} |
| O/N 15/P22/Q4/a,b,c,d,e,f,g | context of O/N 15/P22/Q4/f would exceed one page (862 pt): kept with the parts it depends on | {'11': 14, '10': 1} |
| O/N 15/P23/Q6/c | context for ['(c)(i)', '(c)(ii)', '(c)(iii)'] exceeds one page | {'11': 5, '10': 2} |
| O/N 15/P23/Q8/a,b,c | context of O/N 15/P23/Q8/c would exceed one page (968 pt): kept with the parts it depends on | {'11': 4, '12': 7} |
| O/N 16/P21/Q1/a,b | context of O/N 16/P21/Q1/b would exceed one page (1106 pt): kept with the parts it depends on | {'9': 6, '12': 5} |
| O/N 16/P21/Q1/a,b,c | context of O/N 16/P21/Q1/c would exceed one page (1106 pt): kept with the parts it depends on | {'9': 6, '12': 5, '11': 3} |
| O/N 16/P21/Q4/c,d,e | context of O/N 16/P21/Q4/d would exceed one page (1287 pt): kept with the parts it depends on | {'10': 13, '12': 4} |
| O/N 16/P22/Q1/a,b | context of O/N 16/P22/Q1/b would exceed one page (800 pt): kept with the parts it depends on | {'9': 9, '12': 5} |
| O/N 16/P22/Q1/a,b,c | context of O/N 16/P22/Q1/c would exceed one page (800 pt): kept with the parts it depends on | {'9': 9, '12': 5, '11': 3} |
| O/N 16/P22/Q2/a,b,c,d | context of O/N 16/P22/Q2/d would exceed one page (751 pt): kept with the parts it depends on | {'11': 8, '12': 7} |
| O/N 16/P23/Q1/a,b | context of O/N 16/P23/Q1/b would exceed one page (1106 pt): kept with the parts it depends on | {'9': 6, '12': 5} |
| O/N 16/P23/Q1/a,b,c | context of O/N 16/P23/Q1/c would exceed one page (1106 pt): kept with the parts it depends on | {'9': 6, '12': 5, '11': 3} |
| O/N 16/P23/Q4/c,d,e | context of O/N 16/P23/Q4/d would exceed one page (1287 pt): kept with the parts it depends on | {'10': 13, '12': 4} |
| O/N 17/P21/Q3/c | context for ['(c)(i)'] exceeds one page | {'12': 4, '5': 3} |
| O/N 17/P21/Q3/a,b,c | context of O/N 17/P21/Q3/c would exceed one page (1088 pt): kept with the parts it depends on | {'10': 16, '12': 4, '5': 3} |
| O/N 17/P23/Q3/c | context for ['(c)(i)'] exceeds one page | {'12': 4, '5': 3} |
| O/N 17/P23/Q3/a,b,c | context of O/N 17/P23/Q3/c would exceed one page (1088 pt): kept with the parts it depends on | {'10': 16, '12': 4, '5': 3} |
| O/N 18/P22/Q1/b | (b)(ii) depends on sibling ['(b)(i)'] | {'10': 5, '11': 5} |
| O/N 18/P23/Q1/b | (b)(ii) depends on sibling ['(b)(i)'] | {'10': 5, '11': 5} |

## Lettered parts split by unit

88 lettered parts were split into roman-level items because their sub-parts belong to different units and each is solvable alone:

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
- M/J 15/P11/Q5/c: M/J 15/P11/Q5/c(i) → unit 2; M/J 15/P11/Q5/c(ii) → unit None; M/J 15/P11/Q5/c(iii) → unit 2
- M/J 15/P12/Q5/c: M/J 15/P12/Q5/c(i) → unit 2; M/J 15/P12/Q5/c(ii) → unit None; M/J 15/P12/Q5/c(iii) → unit 2
- M/J 15/P21/Q1/b: M/J 15/P21/Q1/b(i) → unit 9; M/J 15/P21/Q1/b(ii) → unit 11
- M/J 15/P21/Q4: M/J 15/P21/Q4/(i) → unit 11; M/J 15/P21/Q4/(ii) → unit 12
- M/J 15/P22/Q1/b: M/J 15/P22/Q1/b(i) → unit 9; M/J 15/P22/Q1/b(ii) → unit 11
- M/J 15/P22/Q4: M/J 15/P22/Q4/(i) → unit 11; M/J 15/P22/Q4/(ii) → unit 12
- M/J 15/P23/Q2/b: M/J 15/P23/Q2/b(i) → unit 12; M/J 15/P23/Q2/b(ii) → unit 11
- M/J 15/P23/Q3: M/J 15/P23/Q3/(i) → unit 12; M/J 15/P23/Q3/(ii) → unit 11
- M/J 16/P21/Q3/b: M/J 16/P21/Q3/b(i) → unit 10; M/J 16/P21/Q3/b(ii) → unit 11
- M/J 16/P22/Q3/b: M/J 16/P22/Q3/b(i) → unit 10; M/J 16/P22/Q3/b(ii) → unit 11
- M/J 17/P11/Q2/a: M/J 17/P11/Q2/a(i) → unit 3; M/J 17/P11/Q2/a(ii) → unit None
- M/J 17/P11/Q4/d: M/J 17/P11/Q4/d(i) → unit 1; M/J 17/P11/Q4/d(ii) → unit 4
- M/J 17/P11/Q7/c: M/J 17/P11/Q7/c(i,ii,iii,iv) → unit None; M/J 17/P11/Q7/c(v) → unit 6
- M/J 17/P12/Q5/c: M/J 17/P12/Q5/c(i) → unit 1; M/J 17/P12/Q5/c(ii) → unit 4
- M/J 17/P12/Q6/c: M/J 17/P12/Q6/c(i,ii,iii,iv) → unit None; M/J 17/P12/Q6/c(v) → unit 6
- M/J 17/P13/Q2/a: M/J 17/P13/Q2/a(i) → unit 3; M/J 17/P13/Q2/a(ii) → unit None
- M/J 17/P13/Q4/d: M/J 17/P13/Q4/d(i) → unit 1; M/J 17/P13/Q4/d(ii) → unit 4
- M/J 17/P13/Q7/c: M/J 17/P13/Q7/c(i,ii,iii,iv) → unit None; M/J 17/P13/Q7/c(v) → unit 6
- M/J 17/P21/Q1/b: M/J 17/P21/Q1/b(i) → unit 10; M/J 17/P21/Q1/b(ii,iii) → unit 11
- M/J 17/P23/Q1/b: M/J 17/P23/Q1/b(i) → unit 10; M/J 17/P23/Q1/b(ii,iii) → unit 11
- M/J 18/P22/Q2/c: M/J 18/P22/Q2/c(i) → unit 12; M/J 18/P22/Q2/c(ii) → unit 11
- M/J 18/P23/Q2/c: M/J 18/P23/Q2/c(i) → unit 12; M/J 18/P23/Q2/c(ii) → unit 11
- M/J 19/P11/Q2/b: M/J 19/P11/Q2/b(i) → unit 8; M/J 19/P11/Q2/b(ii) → unit None
- M/J 19/P12/Q5/b: M/J 19/P12/Q5/b(i) → unit 6; M/J 19/P12/Q5/b(ii,iii) → unit 8
- M/J 19/P21/Q1/b: M/J 19/P21/Q1/b(i) → unit 11; M/J 19/P21/Q1/b(ii) → unit 10
- M/J 19/P22/Q1/b: M/J 19/P22/Q1/b(i) → unit 11; M/J 19/P22/Q1/b(ii) → unit 10
- M/J 20/P12/Q2/c: M/J 20/P12/Q2/c(i,ii) → unit 5; M/J 20/P12/Q2/c(iii) → unit 4
- M/J 20/P21/Q6/c: M/J 20/P21/Q6/c(i) → unit 11; M/J 20/P21/Q6/c(ii) → unit 12
- M/J 20/P22/Q2/b: M/J 20/P22/Q2/b(i) → unit 9; M/J 20/P22/Q2/b(ii) → unit 12
- M/J 20/P22/Q6/a: M/J 20/P22/Q6/a(i) → unit 11; M/J 20/P22/Q6/a(ii,iii) → unit 12
- M/J 20/P23/Q5/b: M/J 20/P23/Q5/b(i) → unit 10; M/J 20/P23/Q5/b(ii) → unit 12
- M/J 20/P23/Q5/d: M/J 20/P23/Q5/d(i,ii) → unit 12; M/J 20/P23/Q5/d(iii) → unit 5
- 9608 M/J 21/P12/Q5/e: 9608 M/J 21/P12/Q5/e(i) → unit None; 9608 M/J 21/P12/Q5/e(ii) → unit 6
- 9608 M/J 21/P13/Q4/a: 9608 M/J 21/P13/Q4/a(i) → unit 5; 9608 M/J 21/P13/Q4/a(ii) → unit None; 9608 M/J 21/P13/Q4/a(iii) → unit 5
- 9608 M/J 21/P21/Q5/a: 9608 M/J 21/P21/Q5/a(i) → unit 11; 9608 M/J 21/P21/Q5/a(ii) → unit 6
- 9608 M/J 21/P21/Q5/b: 9608 M/J 21/P21/Q5/b(i,ii) → unit 12; 9608 M/J 21/P21/Q5/b(iii) → unit 5
- O/N 15/P11/Q3/b: O/N 15/P11/Q3/b(i) → unit 2; O/N 15/P11/Q3/b(ii) → unit None
- O/N 15/P13/Q3/b: O/N 15/P13/Q3/b(i) → unit 2; O/N 15/P13/Q3/b(ii) → unit None
- O/N 15/P22/Q5/a: O/N 15/P22/Q5/a(i) → unit 12; O/N 15/P22/Q5/a(ii) → unit 10; O/N 15/P22/Q5/a(iii) → unit 11
- O/N 15/P22/Q6/b: O/N 15/P22/Q6/b(i) → unit 9; O/N 15/P22/Q6/b(ii) → unit 11
- O/N 15/P22/Q7/b: O/N 15/P22/Q7/b(i) → unit 11; O/N 15/P22/Q7/b(ii) → unit 9
- O/N 16/P11/Q4: O/N 16/P11/Q4/(i) → unit None; O/N 16/P11/Q4/(ii) → unit 3; O/N 16/P11/Q4/(iii,iv) → unit None
- O/N 16/P13/Q4: O/N 16/P13/Q4/(i) → unit None; O/N 16/P13/Q4/(ii) → unit 3; O/N 16/P13/Q4/(iii,iv) → unit None
- O/N 16/P22/Q5/b: O/N 16/P22/Q5/b(i) → unit 9; O/N 16/P22/Q5/b(ii,iii) → unit 10
- O/N 16/P22/Q5/c: O/N 16/P22/Q5/c(i,ii) → unit 11; O/N 16/P22/Q5/c(iii) → unit 12
- O/N 17/P22/Q1/a: O/N 17/P22/Q1/a(i,ii) → unit 10; O/N 17/P22/Q1/a(iii) → unit None
- O/N 17/P22/Q1/b: O/N 17/P22/Q1/b(i) → unit 1; O/N 17/P22/Q1/b(ii) → unit None
- O/N 18/P13/Q2/b: O/N 18/P13/Q2/b(i,ii,iii) → unit 1; O/N 18/P13/Q2/b(iv) → unit 4
- O/N 18/P22/Q2/a: O/N 18/P22/Q2/a(i) → unit 9; O/N 18/P22/Q2/a(ii) → unit 11
- O/N 18/P22/Q4/a: O/N 18/P22/Q4/a(i) → unit 11; O/N 18/P22/Q4/a(ii) → unit 10
- O/N 18/P23/Q2/a: O/N 18/P23/Q2/a(i) → unit 9; O/N 18/P23/Q2/a(ii) → unit 11
- O/N 18/P23/Q4/a: O/N 18/P23/Q4/a(i) → unit 11; O/N 18/P23/Q4/a(ii) → unit 10
- O/N 18/P23/Q4/d: O/N 18/P23/Q4/d(i) → unit 10; O/N 18/P23/Q4/d(ii) → unit 11
- O/N 19/P11/Q2/a: O/N 19/P11/Q2/a(i,ii,iii) → unit 3; O/N 19/P11/Q2/a(iv) → unit None
- O/N 19/P12/Q6/d: O/N 19/P12/Q6/d(i) → unit 1; O/N 19/P12/Q6/d(ii) → unit None
- O/N 19/P12/Q6/e: O/N 19/P12/Q6/e(i,ii) → unit 2; O/N 19/P12/Q6/e(iii) → unit None
- O/N 19/P13/Q1/c: O/N 19/P13/Q1/c(i) → unit 2; O/N 19/P13/Q1/c(ii) → unit 6
- O/N 19/P13/Q2/b: O/N 19/P13/Q2/b(i,ii) → unit 1; O/N 19/P13/Q2/b(iii) → unit None
- O/N 19/P21/Q1/b: O/N 19/P21/Q1/b(i) → unit 10; O/N 19/P21/Q1/b(ii) → unit 11
- O/N 19/P21/Q6/d: O/N 19/P21/Q6/d(i) → unit 10; O/N 19/P21/Q6/d(ii) → unit 11
- O/N 19/P22/Q1/b: O/N 19/P22/Q1/b(i) → unit 10; O/N 19/P22/Q1/b(ii) → unit 11
- O/N 19/P23/Q1/a: O/N 19/P23/Q1/a(i) → unit 10; O/N 19/P23/Q1/a(ii) → unit 11
- O/N 19/P23/Q2/a: O/N 19/P23/Q2/a(i) → unit 11; O/N 19/P23/Q2/a(ii) → unit 9

## Insert

| Item | Shown as | Why |
|---|---|---|
| M/J 21/P21/Q4/a,c | this paper's insert inline (1 page(s)) | uses UCASE (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| M/J 21/P21/Q4/b | this paper's insert inline (1 page(s)) | uses UCASE (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| M/J 21/P22/Q5/b | this paper's insert inline (1 page(s)) | uses LCASE (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| M/J 21/P23/Q4/a,c | this paper's insert inline (1 page(s)) | uses UCASE (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| M/J 21/P23/Q4/b | this paper's insert inline (1 page(s)) | uses UCASE (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| M/J 23/P22/Q2/a,b | this paper's insert inline (3 page(s)) | text refers to the insert; insert text differs from the Appendix |
| M/J 24/P22/Q1/b | this paper's insert inline (3 page(s)) | text refers to the insert; insert text differs from the Appendix |
| M/J 24/P23/Q1/a,b | this paper's insert inline (3 page(s)) | text refers to the insert; insert text differs from the Appendix |
| M/J 25/P23/Q1/a,b | this paper's insert inline (3 page(s)) | text refers to the insert; insert text differs from the Appendix |
| O/N 21/P22/Q1/c,d | this paper's insert inline (3 page(s)) | text refers to the insert; insert text differs from the Appendix |
| O/N 24/P21/Q6/b | this paper's insert inline (3 page(s)) | text refers to the insert; insert text differs from the Appendix |
| O/N 24/P23/Q6 | this paper's insert inline (3 page(s)) | text refers to the insert; insert text differs from the Appendix |
| O/N 25/P21/Q1/a | this paper's insert inline (3 page(s)) | text refers to the insert; insert text differs from the Appendix |
| M/J 16/P21/Q1/a | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| M/J 16/P21/Q3/a,b(i) | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| M/J 16/P21/Q6/a,b | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| M/J 16/P22/Q1/a | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| M/J 16/P22/Q3/a,b(i) | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| M/J 16/P22/Q6/a,b | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| M/J 16/P23/Q1/a | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| M/J 16/P23/Q2/a,b | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| M/J 16/P23/Q3/a | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| M/J 16/P23/Q6/a,b | this paper's insert inline (1 page(s)) | text refers to the Appendix; uses LCASE, UCASE (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| M/J 17/P21/Q3 | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| M/J 17/P22/Q3 | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| M/J 17/P23/Q3 | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| M/J 18/P21/Q1/b | this paper's insert inline (1 page(s)) | text refers to the Appendix; uses MOD (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| M/J 18/P21/Q2/a | this paper's insert inline (1 page(s)) | uses LCASE (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| M/J 18/P21/Q2/b | this paper's insert inline (1 page(s)) | uses LCASE (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| M/J 18/P22/Q1/b | this paper's insert inline (1 page(s)) | text refers to the Appendix; uses MOD (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| M/J 18/P23/Q1/b | this paper's insert inline (1 page(s)) | text refers to the Appendix; uses MOD (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| M/J 19/P21/Q1/b(i) | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| M/J 19/P21/Q4/a,c | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| M/J 19/P21/Q4/b | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| M/J 19/P21/Q5/b | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| M/J 19/P22/Q1/b(i) | this paper's insert inline (1 page(s)) | text refers to the Appendix; uses NUM_TO_STRING, STRING_TO_NUM (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| M/J 19/P22/Q4/a,b | this paper's insert inline (1 page(s)) | text refers to the Appendix; uses STRING_TO_NUM (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| M/J 19/P23/Q1/b | this paper's insert inline (1 page(s)) | text refers to the Appendix; uses NUM_TO_STRING, STRING_TO_NUM (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| M/J 19/P23/Q5/a,b | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| M/J 20/P21/Q2/a,b | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| M/J 20/P21/Q3/b | this paper's insert inline (1 page(s)) | text refers to the Appendix; uses NUM_TO_STRING (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| M/J 20/P21/Q5/a,b | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| M/J 20/P22/Q3 | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| M/J 20/P22/Q4/a | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| M/J 20/P22/Q6/a(i) | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| M/J 20/P23/Q5/a,b(i) | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| 9608 M/J 21/P21/Q1/a | this paper's insert inline (2 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| 9608 M/J 21/P21/Q1/c | this paper's insert inline (2 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| 9608 M/J 21/P21/Q2/a,b | this paper's insert inline (1 page(s)) | uses LCASE (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| 9608 M/J 21/P21/Q4/a | this paper's insert inline (2 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| 9608 M/J 21/P21/Q4/b | this paper's insert inline (2 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| 9608 M/J 21/P21/Q4/c | this paper's insert inline (2 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| 9608 M/J 21/P21/Q5/a(i) | this paper's insert inline (2 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| 9608 M/J 21/P22/Q1/d | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| 9608 M/J 21/P23/Q1/b,c | this paper's insert inline (2 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| 9608 M/J 21/P23/Q4/a,b,c | this paper's insert inline (2 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| 9608 M/J 21/P23/Q5/a | this paper's insert inline (2 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| O/N 16/P21/Q3/a,b,c,d | this paper's insert inline (2 page(s)) | text refers to the Appendix; uses CHARACTERCOUNT, SUBSTR (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| O/N 16/P22/Q2/a,b,c,d | this paper's insert inline (2 page(s)) | text refers to the Appendix; uses ONECHAR, TONUM (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| O/N 16/P22/Q4/a,b,c | this paper's insert inline (2 page(s)) | text refers to the Appendix; uses RND (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| O/N 16/P22/Q4/d | this paper's insert inline (2 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| O/N 16/P23/Q3/a,b,c,d | this paper's insert inline (2 page(s)) | text refers to the Appendix; uses CHARACTERCOUNT, SUBSTR (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| O/N 17/P21/Q2/a,b | this paper's insert inline (1 page(s)) | text refers to the Appendix; uses MODULUS (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| O/N 17/P21/Q2/c | this paper's insert inline (1 page(s)) | text refers to the Appendix; uses MODULUS (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| O/N 17/P21/Q5/a | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| O/N 17/P22/Q3 | this paper's insert inline (1 page(s)) | uses MODULUS (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| O/N 17/P22/Q5 | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| O/N 17/P23/Q2/a,b | this paper's insert inline (1 page(s)) | text refers to the Appendix; uses MODULUS (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| O/N 17/P23/Q2/c | this paper's insert inline (1 page(s)) | text refers to the Appendix; uses MODULUS (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| O/N 17/P23/Q5/a | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| O/N 18/P22/Q1/b | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| O/N 18/P22/Q2/a(i) | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| O/N 18/P22/Q2/a(ii) | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| O/N 18/P22/Q2/b | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| O/N 18/P23/Q1/b | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| O/N 18/P23/Q2/a(ii) | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| O/N 19/P21/Q1/b(ii) | this paper's insert inline (2 page(s)) | text refers to the Appendix; uses NUM_TO_STRING, STRING_TO_NUM (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| O/N 19/P21/Q3 | this paper's insert inline (2 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| O/N 19/P21/Q4/b | this paper's insert inline (2 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| O/N 19/P22/Q1/b(ii) | this paper's insert inline (1 page(s)) | text refers to the Appendix; uses NUM_TO_STRING (defined in this paper's insert, not in the Appendix); insert text differs from the Appendix |
| O/N 19/P22/Q3/a,b | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| O/N 19/P23/Q5 | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |
| O/N 19/P23/Q6/a,b | this paper's insert inline (1 page(s)) | text refers to the Appendix; insert text differs from the Appendix |

## Context added to items

Besides the stem and the lettered introduction (always shown), earlier parts were added as context for these reasons (count of context parts):

- identifier rule: 28
- part reference: 24
- scenario noun ("the ..."): 4
- material announced in the stem is printed in the first part: 3
- part reference (material printed in a later part): 2

## Thin units (< 5 items)

- None.

## Final checks on the built books

- Coverage: every lowest-level part of every included question appears in exactly one item, or is in an exclusion list above. Unexplained gaps: 0; duplicates: 0.
- Self-containment re-check (build resolver): 0 failures; context recomputed identically for every item (0 mismatches).
- Marks re-check (item [marks] = MS marks): 0 failures.
- Every item reference found on its indexed page: 0 misses; every item has an answer entry: 0 misses.
- Every item is in the book of its unit: 0 misses.

## Layout and visual checks

- Stage 0 (test build of 7 papers) and stage 4 (Phase 1 books): sample pages of every page type were rendered at 60-80 dpi and viewed (cover, contents, unit title page, item pages of both papers, Answers pages, Topic index, Appendix). Fixed then: a block of table definitions and a block of gap-fill pseudocode split across pages; the Appendix banner now takes its reference from the insert's own header.
- Self-check, automated: every crop in both books is compared with its source page pixel by pixel (`audit/scripts/cs/c72_pixels.py`), every placed crop is read back for margins, overlaps and page breaks (`c73_layout.py`), every mark is checked at 300 dpi (`c74_marks.py`). Counts are in `audit/CS_CHECK.md`.
- Self-check, viewed: every automated flag was viewed as a book crop beside its source page. Several rounds of samples of 15 question items and 5 answers per unit were viewed at 92 dpi during the self-check; the last round, on the final books, is recorded in `audit/CS_CHECK.md`.
- Found by viewing and fixed (each has a row in AUTO-DECIDED): labelled answer lines ("Answer ......") and answer cells of tables still showing; gaps in gap-fill pseudocode removed; the bar under a binary sum missing; a trace of footer words or of a removed frame on the edge of a crop; empty hairline frames for drawings still showing; the rule above the copyright paragraph of a last page; a mark, a line ending in a colon, or the opening lines of an item separated from what they belong to by a page break; code listings split across pages; one introduction announcing pseudocode that was not shown.
- Known and left as they are: about 290 pages are less than 55 % full because an item, a figure or an introducing line is not split; the pages of an insert shown with an item, and the Appendix, break between rows of their tables.

