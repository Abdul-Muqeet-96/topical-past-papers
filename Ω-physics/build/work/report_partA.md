## Part A: booklet light check (report only)

Source: `Ω-physics/reference/Physics paper 2 9702 3.pdf` (550 scanned pages), OCR'd into `Ω-physics/reference/booklet-ocr.pdf` (scripts/physics/ocr_booklet.py). Map: scripts/physics/map_booklet.py; checks: scripts/physics/booklet_check.py (results in work/booklet_check.json).

### Contents page vs pages

| Booklet unit | → topic | Title page (contents / found) | Answers Section (contents / found) | Question pages | Items | Answers | Numbered to |
|---|---|---|---|---|---|---|---|
| 1 Physical Quantities And Units | 1 | 5 / 5 | 30 / 30 | 6–29 | 33 | 33 | 33 |
| 2 Measurement Techniques | 1 | 39 / 39 | 59 / 59 | 40–58 | 23 | 23 | 23 |
| 3 Kinematics | 2 | 65 / 65 | 111 / 111 | 66–110 | 32 | 32 | 33 |
| 4 Dynamics | 3 | 123 / 123 | 167 / 167 | 124–166 | 31 | 31 | 33 |
| 5 Forces, Density And Pressure | 4 | 179 / 179 | 222 / 222 | 180–221 | 33 | 33 | 33 |
| 6 Work, Energy And Power | 5 | 233 / 233 | 270 / 270 | 234–269 | 31 | 31 | 31 |
| 7 Deformation Of Solids | 6 | 283 / 283 | 327 / 327 | 284–326 | 32 | 27 | 33 |
| 8 Waves | 7 | 338 / 338 | 362 / 362 | 339–361 | 22 | 22 | 22 |
| 9 Superposition | 8 | 369 / 369 | 410 / 410 | 370–409 | 33 | 33 | 33 |
| 10 Current Of Electricity | 9 | 421 / 421 | 462 / 462 | 422–461 | 33 | 33 | 33 |
| 11 D.C Circuits | 10 | 473 / 473 | 517 / 517 | 474–516 | 33 | 33 | 33 |
| 12 Particle And Nuclear Physics | 11 | 531 / 531 | 552 / 552 | 532–551 | 30 | 30 | 33 |

All 12/12 units start and end where the contents page says (printed page numbers). Items are numbered 1..N per unit in both the question and the answers sections; numbers absent below are explained by the missing scan pages.

### Pages missing from the scan and what they cost

| Printed pages missing | Lost |
|---|---|
| 96–97 | Unit 3 questions #25 |
| 144–145 | Unit 4 questions #16,17 |
| 313–314 | Unit 7 questions #22 |
| 328–329 | Unit 7 answers #5,6,7,8,9 |
| 534–535 | Unit 12 questions #5,6,7 |

| Item | Flag | In the book |
|---|---|---|
| Unit 3 #24 O/N 15/P21/Q3 | scan_gap_q:96-97 | question runs into missing pages 96-97: kept as scanned, note "Incomplete in the scanned booklet" |
| Unit 4 #15 M/J 19/P21/Q2 | scan_gap_q:144-145 | question runs into missing pages 144-145: kept as scanned, note "Incomplete in the scanned booklet" |
| Unit 7 #4 O/N 22/P22/Q4 | scan_gap_a:328-329 | answer runs into missing pages 328-329: kept, note on the answer |
| Unit 7 #5 O/N 22/P21/Q2 | no_answer | answer on missing pages: item kept, note "Answer missing from the scanned booklet" |
| Unit 7 #6 M/J 22/P21/Q4 | no_answer | answer on missing pages: item kept, note "Answer missing from the scanned booklet" |
| Unit 7 #7 O/N 21/P21/Q3 | no_answer | answer on missing pages: item kept, note "Answer missing from the scanned booklet" |
| Unit 7 #8 O/N 21/P23/Q1 | no_answer | answer on missing pages: item kept, note "Answer missing from the scanned booklet" |
| Unit 7 #9 M/J 21/P22/Q1 | no_answer | answer on missing pages: item kept, note "Answer missing from the scanned booklet" |
| Unit 7 #21 O/N 18/P23/Q1 | scan_gap_q:313-314 | question runs into missing pages 313-314: kept as scanned, note "Incomplete in the scanned booklet" |
| Unit 12 #4 MAR 23/P22/Q7 | scan_gap_q:534-535 | question runs into missing pages 534-535: kept as scanned, note "Incomplete in the scanned booklet" |

Answers whose questions are lost (not in the book): Unit 3 #25 (OIN 15/P23/Q3), Unit 4 #16 (MAR 19/P22/Q3), Unit 4 #17 (OIN 18/P22/Q3), Unit 7 #22 (MiJ 18/P21/Q2), Unit 12 #5 (ON 22/P22/Q7), Unit 12 #6 (O/N 22/P21/Q6), Unit 12 #7 (O/N 22/P23/Q6)

### References

- 366/366 item references parse unambiguously (after 1 headings read by image); every answer heading carries the same reference as its item (mismatches: 0).
- Years: 2013: 11, 2014: 23, 2015: 29, 2016: 25, 2017: 32, 2018: 38, 2019: 45, 2020: 47, 2021: 43, 2022: 44, 2023: 29. Items after 2023: 0.
- Duplicates: M/J 19/P21/Q7 (Unit 3 #16 and Unit 12 #28); MAR 20/P22/Q4 (Unit 4 #11 and Unit 9 #16) — both copies kept, noted.

### Sample check against the official papers (55 items, 5 per syllabus topic)

Printed marks were read from each item's right margin (OCR at 300 dpi) and compared with the official QP parsed from its text layer; then booklet crop and official pages were viewed side by side (50 dpi) for missing figures or text. Margin OCR matched the official marks for 46/55; the other 9 were OCR misreads (or the official parser missed a part on an old paper) and the marks were equal on inspection. Problems found per topic: 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0 (no unit reached 3, so no full-unit check was triggered).

| Topic | Item | Official | Printed (OCR) | Visual verdict |
|---|---|---|---|---|
| 1 | Unit 1 #1 M/J 23/P22/Q1 | 6 | 6 | text and figures match the official question; printed marks equal the official marks |
| 1 | Unit 1 #5 M/J 20/P22/Q1 | 6 | 6 | text and figures match the official question; printed marks equal the official marks |
| 1 | Unit 1 #16 O/N 17/P23/Q1 | 5 | 5 | text and figures match the official question; printed marks equal the official marks |
| 1 | Unit 1 #25 M/J 15/P22/Q1 | 6 | 6 | text and figures match the official question; printed marks equal the official marks |
| 1 | Unit 2 #23 O/N 13/P23/Q2 | 6 | 6 | text and figures match the official question; printed marks equal the official marks |
| 2 | Unit 3 #1 M/J 23/P23/Q1 | 7 | 7 | text and figures match the official question; printed marks equal the official marks |
| 2 | Unit 3 #9 O/N 20/P22/Q1 | 6 | 6 | text and figures match the official question; printed marks equal the official marks |
| 2 | Unit 3 #16 M/J 19/P21/Q7 | 5 | 5 | alpha-scattering / quark question filed by the booklet under Kinematics (also its Unit 12 #28); content and marks match |
| 2 | Unit 3 #23 O/N 15/P22/Q2 | 10 | 10 | text and figures match the official question; printed marks equal the official marks |
| 2 | Unit 3 #33 M/J 13/P23/Q2 | 11 | 11 | text and figures match the official question; printed marks equal the official marks |
| 3 | Unit 4 #1 M/J 23/P22/Q3 | 10 | 10 | text and figures match the official question; printed marks equal the official marks |
| 3 | Unit 4 #8 M/J 21/P21/Q2 | 12 | 15 | text and figures match the official question; printed marks equal the official marks |
| 3 | Unit 4 #18 O/N 18/P21/Q2 | 6 | 6 | text and figures match the official question; printed marks equal the official marks |
| 3 | Unit 4 #26 O/N 16/P22/Q2 | 12 | 12 | text and figures match the official question; printed marks equal the official marks |
| 3 | Unit 4 #33 O/N 14/P22/Q1/c | 5 | 5 | booklet prints part (c) relabelled as (a); content and marks (5) match |
| 4 | Unit 5 #1 M/J 23/P22/Q2 | 12 | 12 | text and figures match the official question; printed marks equal the official marks |
| 4 | Unit 5 #9 MAR 22/P22/Q3 | 7 | 7 | text and figures match the official question; printed marks equal the official marks |
| 4 | Unit 5 #17 M/J 20/P23/Q3 | 11 | 11 | text and figures match the official question; printed marks equal the official marks |
| 4 | Unit 5 #25 O/N 17/P22/Q2 | 5 | 5 | text and figures match the official question; printed marks equal the official marks |
| 4 | Unit 5 #33 M/J 15/P22/Q3 | 6 | 6 | text and figures match the official question; printed marks equal the official marks |
| 5 | Unit 6 #1 M/J 23/P21/Q2/c | 7 | 7 | booklet prints part (c) relabelled as (a); content and marks (7) match |
| 5 | Unit 6 #9 O/N 21/P22/Q3 | 8 | 8 | text and figures match the official question; printed marks equal the official marks |
| 5 | Unit 6 #16 MAR 19/P22/Q2 | 11 | 11 | text and figures match the official question; printed marks equal the official marks |
| 5 | Unit 6 #23 O/N 15/P23/Q8 | 6 | 6 | text and figures match the official question; printed marks equal the official marks |
| 5 | Unit 6 #31 M/J 13/P21/Q3 | 11 | 11 | text and figures match the official question; printed marks equal the official marks |
| 6 | Unit 7 #1 M/J 23/P22/Q4 | 5 | 5 | text and figures match the official question; printed marks equal the official marks |
| 6 | Unit 7 #13 O/N 20/P21/Q4 | 9 | 9 | text and figures match the official question; printed marks equal the official marks |
| 6 | Unit 7 #19 M/J 19/P22/Q2/c,d | 5 | 5 | booklet prints parts (c),(d) relabelled as (a),(b); content and marks (5) match |
| 6 | Unit 7 #27 M/J 17/P22/Q3 | 4 | 4 | text and figures match the official question; printed marks equal the official marks |
| 6 | Unit 7 #33 O/N 15/P23/Q7 | 5 | 5 | text and figures match the official question; printed marks equal the official marks |
| 7 | Unit 8 #1 M/J 23/P22/Q5 | 9 | 12 | text and figures match the official question; printed marks equal the official marks |
| 7 | Unit 8 #6 M/J 22/P21/Q5 | 8 | 6 | text and figures match the official question; printed marks equal the official marks |
| 7 | Unit 8 #11 M/J 20/P23/Q4 | 10 | 10 | text and figures match the official question; printed marks equal the official marks |
| 7 | Unit 8 #17 O/N 15/P21/Q5 | 7 | 7 | text and figures match the official question; printed marks equal the official marks |
| 7 | Unit 8 #22 O/N 13/P23/Q5 | 9 | 9 | text and figures match the official question; printed marks equal the official marks |
| 8 | Unit 9 #1 M/J 23/P21/Q5 | 9 | 8 | text and figures match the official question; printed marks equal the official marks |
| 8 | Unit 9 #9 M/J 21/P21/Q4 | 10 | 10 | text and figures match the official question; printed marks equal the official marks |
| 8 | Unit 9 #17 O/N 19/P22/Q5 | 9 | 9 | content and marks match; the item number sits left of x=16 pt on this skewed page (crop width taken from ink in the build) |
| 8 | Unit 9 #25 O/N 18/P21/Q4 | 11 | 11 | text and figures match the official question; printed marks equal the official marks |
| 8 | Unit 9 #33 O/N 16/P22/Q4 | 10 | 10 | text and figures match the official question; printed marks equal the official marks |
| 9 | Unit 10 #1 M/J 23/P22/Q6 | 5 | 5 | text and figures match the official question; printed marks equal the official marks |
| 9 | Unit 10 #9 MAR 21/P22/Q6/a,b(i,ii,iii) | 8 | 6 | text and figures match the official question; printed marks equal the official marks |
| 9 | Unit 10 #17 O/N 18/P23/Q6 | 4 | 4 | text and figures match the official question; printed marks equal the official marks |
| 9 | Unit 10 #25 M/J 16/P21/Q6 | 12 | 12 | text and figures match the official question; printed marks equal the official marks |
| 9 | Unit 10 #33 M/J 14/P21/Q6 | 11 | 11 | text and figures match the official question; printed marks equal the official marks |
| 10 | Unit 11 #1 MAR 23/P22/Q6 | 12 | 12 | text and figures match the official question; printed marks equal the official marks |
| 10 | Unit 11 #9 M/J 21/P21/Q5 | 11 | 11 | text and figures match the official question; printed marks equal the official marks |
| 10 | Unit 11 #17 O/N 19/P23/Q6 | 8 | 11 | text and figures match the official question; printed marks equal the official marks |
| 10 | Unit 11 #25 MAR 18/P22/Q5 | 10 | 10 | text and figures match the official question; printed marks equal the official marks |
| 10 | Unit 11 #33 O/N 14/P23/Q6 | 10 | 9 | text and figures match the official question; printed marks equal the official marks |
| 11 | Unit 12 #1 M/J 23/P22/Q8 | 6 | 6 | text and figures match the official question; printed marks equal the official marks |
| 11 | Unit 12 #12 O/N 21/P22/Q7 | 10 | 10 | text and figures match the official question; printed marks equal the official marks |
| 11 | Unit 12 #19 O/N 20/P21/Q8/a,b | 4 | 3 | (b)(ii) mark [1] printed on the line of heading 20: the crop now takes that line (heading whited out); content and marks (4) match |
| 11 | Unit 12 #26 O/N 19/P23/Q7 | 5 | 7 | text and figures match the official question; printed marks equal the official marks |
| 11 | Unit 12 #33 M/J 18/P21/Q7 | 6 | 6 | content and marks match; tests a beta-particle in a uniform electric field (flagged: outside the 2025-27 AS syllabus) |

### Flagged: may be outside the 2025–27 AS syllabus (kept, grey note in the book)

| Item | Reason |
|---|---|
| Unit 1 #8 O/N 19/P22/Q1 | (b) electric field strength of a point charge |
| Unit 6 #14 O/N 19/P23/Q3 | (b) charged particle between charged plates |
| Unit 10 #19 O/N 17/P22/Q5 | (b),(c) smoke particle in the uniform field between charged plates |
| Unit 12 #14 M/J 21/P22/Q6 | (d),(e) alpha-particles / nuclei in a uniform electric field |
| Unit 12 #15 M/J 21/P21/Q6 | (b) nuclei accelerated by a uniform electric field |
| Unit 12 #16 M/J 21/P23/Q6 | (c) proton and alpha-particle in a uniform electric field |
| Unit 12 #22 M/J 20/P21/Q6/b | (b)(ii) electric force on an ion between charged plates |
| Unit 12 #27 M/J 19/P22/Q6 | electric field lines and field strength |
| Unit 12 #33 M/J 18/P21/Q7 | beta-particle path in a uniform electric field |

