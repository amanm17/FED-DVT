#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path

PRODUCTS=Path('public/data/products'); OUT=Path('data/qa')

def close(a,b,tol=1e-6):
    if a is None or b is None:return True
    return abs(float(a)-float(b)) <= max(tol,abs(float(b))*1e-8)

def check_product(path:Path):
    p=json.loads(path.read_text()); hs=p['product']['hs6']; issues=[]; warnings=[]
    years=p.get('period',{}).get('years') or list(range(p['period']['start'],p['period']['end']+1)); yearly=p.get('yearly',{})
    if len(hs)!=6 or not hs.isdigit():issues.append('HS code is not six numeric digits')
    for y in years:
        s=yearly.get(str(y))
        if not s:
            issues.append(f'{y}: missing yearly snapshot'); continue
        ind=s['india']; glob=s['global']; sup=s.get('suppliers',[]); dst=s.get('destinations',[])
        if ind['imports']<0 or ind['exports']<0:issues.append(f'{y}: negative India trade value')
        if not close(ind['tradeBalance'],ind['exports']-ind['imports']):issues.append(f'{y}: trade balance mismatch')
        for label,rows,total in [('suppliers',sup,ind['imports']),('destinations',dst,ind['exports'])]:
            vals=[float(r['value']) for r in rows]
            shares=[float(r['share']) for r in rows]
            if vals != sorted(vals,reverse=True):issues.append(f'{y}: {label} not sorted descending')
            if any(x<0 or x>100.0001 for x in shares):issues.append(f'{y}: invalid {label} share')
            if sum(shares)>100.5:warnings.append(f'{y}: top {label} shares sum to {sum(shares):.2f}% (>100.5%)')
            if rows and total>0 and not close(rows[0]['share'],rows[0]['value']/total*100,tol=.01):issues.append(f'{y}: {label} leading share/value mismatch')
        c=ind.get('supplierConcentration',{})
        if c.get('hhi') is not None and not (0<=c['hhi']<=1.0001):issues.append(f'{y}: HHI outside [0,1]')
        if c.get('largestShare') is not None and c.get('top3Share') is not None and c['top3Share']+1e-6<c['largestShare']:issues.append(f'{y}: top3 share below largest share')
        for label in ['topExporters','topImporters']:
            rows=glob.get(label,[]) or []
            ranks=[r['rank'] for r in rows]
            vals=[float(r['value']) for r in rows]
            if ranks and ranks!=list(range(1,len(ranks)+1)):issues.append(f'{y}: {label} rank sequence invalid')
            if vals!=sorted(vals,reverse=True):issues.append(f'{y}: {label} values not sorted descending')
            if sum(float(r['share']) for r in rows)>100.5:warnings.append(f'{y}: {label} shares exceed 100.5%')
        if glob.get('indiaExportShare') is not None and not 0<=glob['indiaExportShare']<=100:issues.append(f'{y}: India export share outside [0,100]')
        if glob.get('indiaImportShare') is not None and not 0<=glob['indiaImportShare']<=100:issues.append(f'{y}: India import share outside [0,100]')
        if glob.get('indiaExportRank') is not None and glob.get('reporterCount') and not 1<=glob['indiaExportRank']<=glob['reporterCount']:issues.append(f'{y}: export rank outside reporter count')
    latest=str(p['period']['latest'])
    if latest in yearly:
        if not close(p['india']['imports'],yearly[latest]['india']['imports']):issues.append('top-level latest India imports differ from yearly latest')
        if p['global'].get('indiaExportRank')!=yearly[latest]['global'].get('indiaExportRank'):issues.append('top-level latest export rank differs from yearly latest')
    trend={str(x['year']):x for x in p.get('trend',[])}
    for y,s in yearly.items():
        t=trend.get(y)
        if not t:issues.append(f'{y}: trend point missing');continue
        if not close(t.get('indiaImports'),s['india']['imports']):issues.append(f'{y}: trend import mismatch')
        if not close(t.get('indiaExports'),s['india']['exports']):issues.append(f'{y}: trend export mismatch')
        if not close(t.get('reportedWorldExports'),s['global'].get('reportedWorldExports')):issues.append(f'{y}: trend world export mismatch')
    return {'hs6':hs,'status':'FAIL' if issues else ('WARN' if warnings else 'PASS'),'issues':issues,'warnings':warnings,'years':len(years),'generatedAt':p.get('generatedAt')}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--hs');a=ap.parse_args(); files=[PRODUCTS/f'{a.hs}.json'] if a.hs else sorted(PRODUCTS.glob('*.json')); OUT.mkdir(parents=True,exist_ok=True)
    rows=[check_product(f) for f in files if f.exists()]
    (OUT/'qa_report.json').write_text(json.dumps(rows,indent=2))
    with (OUT/'qa_report.csv').open('w',newline='') as fh:
        w=csv.DictWriter(fh,fieldnames=['hs6','status','years','issues','warnings','generatedAt']);w.writeheader()
        for r in rows:w.writerow({**r,'issues':' | '.join(r['issues']),'warnings':' | '.join(r['warnings'])})
    counts={k:sum(r['status']==k for r in rows) for k in ['PASS','WARN','FAIL']}
    print(f"QA complete: {len(rows)} products | PASS {counts['PASS']} | WARN {counts['WARN']} | FAIL {counts['FAIL']}")
    print('Reports: data/qa/qa_report.json, data/qa/qa_report.csv')
    if counts['FAIL']:
        for r in rows:
            if r['status']=='FAIL': print(f"  FAIL {r['hs6']}: " + '; '.join(r['issues'][:3]))
        raise SystemExit(2)
if __name__=='__main__':main()
