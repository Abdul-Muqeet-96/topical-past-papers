"""Check 1b: re-download a random sample (seed 9701) of 10 source PDFs and compare SHA-256 with hub/data/."""
import random, json, subprocess, hashlib, sys, os
rows=[r for r in json.load(open('hub/audit/out/sources.json')) if r['status']!='MISSING']
random.seed(9701); smp=random.sample(rows,10); out=[]
for r in smp:
    b=os.path.basename(r['file']); dst=os.path.join(sys.argv[1],b)
    url='https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/'+b
    code=subprocess.run(['curl','-sS','-L','-o',dst,'-w','%{http_code}','--max-time','120',url],capture_output=True,text=True).stdout
    h=lambda p: hashlib.sha256(open(p,'rb').read()).hexdigest() if os.path.exists(p) else None
    a,c=h(r['file']),h(dst); out.append({'file':b,'http':code,'local_sha256':a,'remote_sha256':c,'identical':a==c,'local_size':os.path.getsize(r['file']),'remote_size':os.path.getsize(dst) if c else None})
    print(b,code,'IDENTICAL' if a==c else 'DIFFERENT')
json.dump(out,open('hub/audit/out/redownload.json','w'),indent=1)
