## How the checks were run

- Every script reads the raw downloads in `data/` and the finished books; none imports the build code. The question-paper and mark-scheme readers (`c20`, `c21`) are written separately from the build's readers, so a part boundary or a mark read wrongly by the build shows as a difference in `c22`.
- Every crop in the books is a Form XObject whose bounding box is the clip on the source page. `c70` reads those boxes back from the book PDFs and maps each crop to its source page; `c72` then renders every crop from the book and from the raw source page at 110 dpi and compares them pixel by pixel (best of 25 one-pixel shifts, one pixel of tolerance): ink that disappeared, ink that appeared, dotted lines, footer words, site stamps, marks.
- Dotted lines: `c72` holds its own statement of the rule that tells an answer line from a gap to fill (text before and after the run, monospace font, table borders, an arrow drawn between a name and the run) and reports an answer line that is still visible or a gap that was removed. Runs that the rule leaves to the surrounding block of code are counted, not judged.
- Layout: `c73` reads the placed crops page by page: margins, overlaps, a heading, a mark or an introducing line left alone, a figure or a code block split across pages, pages with much unused space and the reason for it.
- Topics: `c90` writes every item without its unit, section or outcome, in shuffled order; the items were tagged again from that text alone, then `c91` compares. Disagreements were resolved by reading the whole item (`audit/out/cs/blind/resolved.txt`).
- The checks were repeated after every rebuild (`run_all.sh`); the figures above are from the last run, on the books of this commit.

## What the self-check found and what was changed

Found by the checks above or by viewing, and fixed in the build (each has a row in AUTO-DECIDED in `λ-cs/report.md`):

- two questions (9608 M/J 18/P21 Q6, Q7) excluded although their marks are printed ("Max2", "MAX8"); two items of 9608 M/J 21/P21 Q2 lost to a mark-scheme label;
- nine papers printed at reduced scale were enlarged by 0.8 %;
- answer-line dots removed from the text layer moved other glyphs on some pages (now verified page by page, with a fallback);
- a mark on the footer line clipped by a white rectangle; barcode strips inside two items; frames of logic circuits to draw erased as empty boxes;
- running-text mark schemes (2015-16): blank tails of rows, footers inside appendix answers, a flowchart box and a fraction cut at the start of a row;
- dotted lines: labelled answer lines ("Answer ......") and answer cells of tables left visible; gaps in gap-fill pseudocode and in sentences removed; a semicolon half covered;
- the bar under a binary sum dropped; a trace of footer words or of a removed frame on the edge row of a crop;
- page breaks: code listings split, a mark, an introducing line or an opening line separated from what it belongs to;
- items.jsonl without the text of insert pages printed with an item; footer words left in the PDF text layer.
