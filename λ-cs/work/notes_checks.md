Causes (inspected, and confirmed by the self-check's independent readers `audit/scripts/cs/c20_qp_parse.py`, `c21_ms_parse.py`, `c22_compare.py`):
- M/J 25/P12 Q7 (9618): the mark-scheme row 7(b)(ii) prints no value in its Marks column (source defect), so the MS marks of Q7 are 7 against 8 in the question paper.
- M/J 15/P23 Q1 (9608): the running-text mark scheme prints 7 marks for the question against 9 in the question paper (part (a) carries one [1] for a 3-mark part).
- O/N 17/P21 and P23 Q1 (9608, identical papers): the mark scheme prints 2 for part 1(a)(ii), the question paper [1].
Nothing is patched: each of these questions is excluded.

Found and corrected by the self-check: M/J 18/P21 Q6 and Q7 (9608) had first been excluded because rows 6(a)(i), 6(b) and 7 seemed to print no mark; their Marks column reads "Max2", "MAX8" and "Max7" (one word). The reader now takes these as marks and both questions are in the books. 9608 M/J 21/P21 Q2 had lost both its items because its first mark-scheme row is labelled "2" instead of "2(a)"; the row is now read as 2(a) (the only part without a row, equal marks; logged above as a label fix).
