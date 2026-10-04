#!/bin/bash
# Check 10 FILE: qpdf --check, pdffonts (embedded), page sizes, file sizes for book + unit PDFs
out=audit/out/file_checks.txt; : > $out
for f in Δ-chemistry/p2-topical-workbook/*.pdf Δ-chemistry/p2-topical-workbook/units/*.pdf; do
  q=$(qpdf --check "$f" 2>&1 | tail -1)
  ne=$(pdffonts "$f" 2>/dev/null | awk 'NR>2 && $(NF-4)=="no"' | wc -l)
  nf=$(pdffonts "$f" 2>/dev/null | awk 'NR>2' | wc -l)
  sz=$(stat -c %s "$f")
  sizes=$(pdfinfo -f 1 -l 99999 "$f" 2>/dev/null | grep "size:" | awk '{print $4"x"$6}' | sort | uniq -c | tr '\n' ';')
  echo "$(basename "$f")|qpdf:$q|fonts:$nf|not_embedded:$ne|bytes:$sz|pagesizes:$sizes" >> $out
done
cat $out | cut -c1-250
