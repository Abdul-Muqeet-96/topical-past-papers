"""Render selected pages of a PDF side by side to one PNG (for inspection).
usage: render_pages.py pdf dpi out.png page [page ...]   (0-based pages)"""
import sys
import pymupdf


def sheet(pdf, dpi, out, pages, cols=None):
    d = pymupdf.open(pdf) if isinstance(pdf, str) else pdf
    pages = [p for p in pages if 0 <= p < d.page_count]
    cols = cols or len(pages)
    rows = (len(pages) + cols - 1) // cols
    w, h = d[pages[0]].rect.width, d[pages[0]].rect.height
    gap = 6
    s = pymupdf.open()
    pg = s.new_page(width=cols * w + (cols - 1) * gap, height=rows * h + (rows - 1) * gap)
    pg.draw_rect(pg.rect, color=None, fill=(0.7, 0, 0))
    for i, p in enumerate(pages):
        x, y = (i % cols) * (w + gap), (i // cols) * (h + gap)
        r = pymupdf.Rect(x, y, x + w, y + h)
        pg.draw_rect(r, color=None, fill=(1, 1, 1))
        pg.show_pdf_page(r, d, p)
    pg.get_pixmap(dpi=dpi).save(out)


if __name__ == "__main__":
    sheet(sys.argv[1], int(sys.argv[2]), sys.argv[3], [int(x) for x in sys.argv[4:]])
