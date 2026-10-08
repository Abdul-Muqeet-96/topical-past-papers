"""Checks 4/9: parse the final book. Unit title pages, Answers banners, running headers,
page labels, and every item heading 'n. REF' (question side and answers side) with page + y."""
import pymupdf as f, re, json, sys
sys.path.insert(0,'hub/audit/scripts'); from a03_lines import lines
B='Δ-chemistry/booklets/p2-topical-workbook/Chemistry-9701-P2-Topical-Workbook.pdf'
REF=re.compile(r'^(\d+)\.\s+((?:M/J|O/N|MAR)\s\d\d/P\d\d/Q\d+\S*)\s*$')
def parse(path):
    d=f.open(path); out={'pages':[],'items':[]}
    for i,p in enumerate(d):
        L=lines(p); txt=p.get_text()
        head=[l for l in L if l['c']<35]
        ht=[' '.join(w[4] for w in l['w']) for l in head]
        pg={'i':i+1,'header':ht,'label':p.get_label(),'w':p.rect.width,'h':p.rect.height}
        m=re.match(r'\s*Unit (\d+)\n',txt)
        if 'items ·' in txt and m: pg['unit_title']=int(m.group(1))
        if re.search(r'^Answers Section$',txt,re.M) and not txt.startswith('Contents'): pg['answers_banner']=True
        out['pages'].append(pg)
        for l in L:
            t=' '.join(w[4] for w in l['w']); mm=REF.match(t)
            if mm: out['items'].append({'n':int(mm.group(1)),'ref':mm.group(2),'page':i+1,'y':round(l['c'],1),'x':round(l['w'][0][0],1)})
    return out
if __name__=='__main__':
    o=parse(B); json.dump(o,open('hub/audit/out/book_parse.json','w'))
    print(len(o['pages']),'pages;',len(o['items']),'item headings;','unit titles',[p['i'] for p in o['pages'] if 'unit_title' in p][:30])
    print('answer banners',[p['i'] for p in o['pages'] if p.get('answers_banner')][:40])
