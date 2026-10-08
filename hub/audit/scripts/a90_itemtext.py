"""Extract each item's visible text from the book (question side and answer side): words between its
heading and the next heading. Text under the build's white-outs (hidden dotted lines) is dropped by
checking rendered ink. Output hub/audit/out/item_text.json."""
import pymupdf as f, json, re
bi=sorted(json.load(open('hub/audit/out/book_items.json')),key=lambda i:(i['page'],i['y']))
d=f.open('Δ-chemistry/booklets/p2-topical-workbook/Chemistry-9701-P2-Topical-Workbook.pdf')
words={}
for i in range(len(d)):
    words[i+1]=[w for w in d[i].get_text('words') if w[1]>46]
out={}
for k,it in enumerate(bi):
    nx=bi[k+1] if k+1<len(bi) else None
    end_pg=nx['page'] if nx else it['page']
    T=[]
    for pg in range(it['page'],end_pg+1):
        y0=it['y']+6 if pg==it['page'] else 0
        y1=nx['y']-6 if (nx and pg==nx['page']) else 9999
        ws=[w for w in words[pg] if y0<w[1]<y1 and not re.fullmatch(r'[.…]{3,}',w[4])]
        ws.sort(key=lambda w:(round(w[3]/4),w[0]))
        L=[];prev=None
        for w in ws:
            k2=round(w[3]/4)
            if prev is not None and k2!=prev: L.append('\n')
            L.append(w[4]); prev=k2
        T.append(' '.join(L).replace(' \n ','\n'))
        if nx and pg==nx['page']: break
    out[it['ref']+'|'+it['side']]={'ref':it['ref'],'side':it['side'],'unit':it['unit'],'n':it['n'],'page':it['page'],'text':'\n'.join(T)}
json.dump(out,open('hub/audit/out/item_text.json','w'))
print(len(out),'item texts')
