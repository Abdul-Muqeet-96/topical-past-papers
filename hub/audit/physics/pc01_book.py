"""Parse the built book: item headings on question and answer sides (page, y, unit, booklet tag)."""
from pc_common import parse, save, BOOK
o = parse(BOOK)
save('book_parse.json', o)
items = [i for i in o['items'] if i['unit']]
qb = {(i['unit'], i['n']): i['booklet'] for i in items if i['side'] == 'Q'}
for i in items:                      # answer headings carry no source tag: take it from the question side
    if i['side'] == 'A':
        i['booklet'] = qb.get((i['unit'], i['n']), False)
save('book_items.json', items)
q = [i for i in items if i['side'] == 'Q']
print(len(o['pages']), 'pages;', len(q), 'question headings (', sum(i['booklet'] for i in q), 'booklet ),',
      sum(1 for i in items if i['side'] == 'A'), 'answer headings; unit titles',
      [p['i'] for p in o['pages'] if 'unit_title' in p])
