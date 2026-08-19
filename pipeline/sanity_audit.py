#!/usr/bin/env python3
import json,math
from pathlib import Path
P=Path('public/data/products')
fails=[];warn=[];passed=0
for f in sorted(P.glob('*.json')):
    try:d=json.loads(f.read_text())
    except Exception as e:fails.append((f.stem,f'Invalid JSON: {e}'));continue
    hs=d.get('product',{}).get('hs6',f.stem); errs=[]; ws=[]
    i=d.get('india',{}); g=d.get('global',{})
    imp=float(i.get('imports') or 0); exp=float(i.get('exports') or 0); bal=i.get('tradeBalance')
    if bal is None or not math.isclose(float(bal),exp-imp,rel_tol=1e-9,abs_tol=1):errs.append('trade balance mismatch')
    ls=i.get('largestSupplier') or {}; sc=i.get('supplierConcentration') or {}
    if ls and sc.get('largestShare') is not None and abs(float(ls.get('share',0))-float(sc['largestShare']))>0.05:errs.append('largest supplier share mismatch')
    if sc.get('top3Share') is not None and sc.get('largestShare') is not None and sc['top3Share']+1e-9<sc['largestShare']:errs.append('top3 share < largest share')
    if sc.get('hhi') is not None and not (0<=float(sc['hhi'])<=1.000001):errs.append('HHI outside [0,1]')
    cov=sc.get('partnerCoverage')
    if cov is not None and (cov<80 or cov>105):ws.append(f'partner coverage {cov:.1f}%')
    if g.get('available'):
        if not g.get('comparisonYear'):errs.append('global metrics shown without comparisonYear')
        if g.get('coverageStatus')!='validated':errs.append('global metrics shown without validated coverage')
        share=g.get('indiaExportShare')
        if share is not None and not (0<=float(share)<=100):errs.append('India export share outside [0,100]')
        top=g.get('topExporters') or []
        vals=[x.get('value',0) for x in top]
        if vals!=sorted(vals,reverse=True):errs.append('top exporters not descending')
        ranks=[x.get('rank') for x in top]
        if ranks and ranks!=list(range(1,len(ranks)+1)):errs.append('top exporter ranks non-sequential')
    else:
        if g.get('indiaExportRank') is not None or g.get('indiaExportShare') is not None or g.get('reportedWorldExports') is not None:errs.append('withheld global block contains derived metrics')
    if errs:fails.append((hs,'; '.join(errs)))
    else:passed+=1
    for x in ws:warn.append((hs,x))
print(f'Sanity audit: {passed} pass | {len(warn)} warnings | {len(fails)} failures')
for hs,m in warn:print(f'  WARN {hs}: {m}')
for hs,m in fails:print(f'  FAIL {hs}: {m}')
Path('data/qa').mkdir(parents=True,exist_ok=True)
Path('data/qa/sanity_audit.json').write_text(json.dumps({'pass':passed,'warnings':[{'hs':h,'message':m} for h,m in warn],'failures':[{'hs':h,'message':m} for h,m in fails]},indent=2))
raise SystemExit(1 if fails else 0)
