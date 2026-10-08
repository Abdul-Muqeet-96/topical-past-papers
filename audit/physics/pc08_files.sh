#!/bin/bash
# File checks: qpdf --check, fonts embedded, page sizes, file sizes (book, unit PDFs, booklet-ocr.pdf)
out=audit/physics/out/file_checks.txt; : > $out
for f in Ω-physics/p2-topical-workbook/*.pdf Ω-physics/p2-topical-workbook/units/*.pdf Ω-physics/booklet-ocr.pdf; do
  q=$(qpdf --check "$f" 2>&1 | tail -1)
  ne=$(pdffonts "$f" 2>/dev/null | awk 'NR>2 && $(NF-4)=="no"' | wc -l)
  nf=$(pdffonts "$f" 2>/dev/null | awk 'NR>2' | wc -l)
  sz=$(stat -c %s "$f")
  pages=$(pdfinfo "$f" 2>/dev/null | awk '/^Pages:/{print $2}')
  echo "$(basename "$f")|qpdf:$q|fonts:$nf|not_embedded:$ne|bytes:$sz|pages:$pages" >> $out
done
cat $out
