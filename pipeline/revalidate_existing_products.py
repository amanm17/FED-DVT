#!/usr/bin/env python3
from __future__ import annotations
import json, math, re
from pathlib import Path
import pandas as pd

RAW=Path('data/raw/comtrade')
PUBLIC=Path('public/data/products')
PROCESSED=Path('data/processed')
REPORT=Path('data/qa/revalidation_report.json')
INDIA='699'


def base(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or not isinstance(df,pd.DataFrame) or df.empty:
        return pd.DataFrame()
    z=df.copy()
    for c,v in [('partner2Code',0),('motCode',0)]:
        if c in z.columns:
            z=z[z[c].fillna(v).astype(str)==str(v)]
    if 'customsCode' in z.columns and (z['customsCode'].astype(str)=='C00').any():
        z=z[z['customsCode'].astype(str)=='C00']
    if 'primaryValue' not in z.columns:
        return pd.DataFrame()
    z['primaryValue']=pd.to_numeric(z['primaryValue'],errors='coerce')
    return z


def reporting_economy(r) -> bool:
    iso=str(r.get('reporterISO',''))
    return len(iso)==3 and iso.isalpha() and iso!='WLD'


def reporter_frame(df: pd.DataFrame, year: int) -> pd.DataFrame:
    if df is None or df.empty or 'refYear' not in df.columns:
        return pd.DataFrame(columns=['reporterCode','reporterDesc','reporterISO','primaryValue'])
    z=base(df)
    if z.empty:return z
    z=z[pd.to_numeric(z['refYear'],errors='coerce')==year].copy()
    if 'partnerCode' in z.columns:
        z=z[z['partnerCode'].astype(str)=='0']
    z=z[z.apply(reporting_economy,axis=1)]
    if z.empty:return z
    z=z[z['primaryValue'].fillna(-1)>=0]
    z=z.sort_values('primaryValue',ascending=False).drop_duplicates('reporterCode').reset_index(drop=True)
    return z


def ranking(df, year):
    cur=reporter_frame(df,year)
    if cur.empty:
        return {'total':None,'indiaRank':None,'indiaShare':None,'leader':None,'leaderShare':None,'count':0,'top':[]}
    total=float(cur['primaryValue'].fillna(0).sum())
    india=cur[cur['reporterCode'].astype(str)==INDIA]
    iv=float(india.iloc[0]['primaryValue']) if not india.empty else None
    rank=int((cur['primaryValue'].astype(float)>iv).sum()+1) if iv is not None else None
    top=[]
    for idx,r in cur.head(10).iterrows():
        v=float(r['primaryValue'] or 0)
        top.append({'code':int(r['reporterCode']),'iso':None if pd.isna(r.get('reporterISO')) else str(r.get('reporterISO')),'name':str(r.get('reporterDesc')),'value':v,'share':v/total*100 if total else 0,'rank':idx+1})
    leader=top[0] if top else None
    return {'total':total,'indiaRank':rank,'indiaShare':iv/total*100 if iv is not None and total else None,'leader':leader['name'] if leader else None,'leaderShare':leader['share'] if leader else None,'count':len(cur),'top':top}


def coverage(df,year,prev_year,top_n=20):
    cur=reporter_frame(df,year); prev=reporter_frame(df,prev_year)
    if cur.empty or prev.empty:
        return {'valid':False,'reason':'Insufficient adjacent-year reporter data','reporterCount':len(cur),'previousReporterCount':len(prev),'reporterCountRatio':None,'top5Present':0,'weightedTop20Coverage':None,'previousLeaderPresent':False}
    cur_codes=set(cur['reporterCode'].astype(str))
    top=prev.head(top_n); denom=float(top['primaryValue'].sum())
    weighted=float(top[top['reporterCode'].astype(str).isin(cur_codes)]['primaryValue'].sum()/denom) if denom>0 else 0.0
    top5_present=int(prev.head(5)['reporterCode'].astype(str).isin(cur_codes).sum())
    leader=str(prev.iloc[0]['reporterCode']) in cur_codes
    ratio=len(cur)/len(prev) if len(prev) else None
    valid=bool(leader and top5_present>=4 and weighted>=0.90 and ratio is not None and ratio>=0.75)
    reasons=[]
    if not leader:reasons.append(f'prior leader {prev.iloc[0].get("reporterDesc")} missing')
    if top5_present<4:reasons.append(f'only {top5_present}/5 prior top reporters present')
    if weighted<0.90:reasons.append(f'prior top-{top_n} value coverage {weighted:.1%}')
    if ratio is None or ratio<0.75:reasons.append(f'reporter-count ratio {ratio:.1%}' if ratio is not None else 'reporter-count ratio unavailable')
    return {'valid':valid,'reason':'; '.join(reasons) if reasons else 'Coverage checks passed','reporterCount':len(cur),'previousReporterCount':len(prev),'reporterCountRatio':ratio,'top5Present':top5_present,'weightedTop20Coverage':weighted,'previousLeaderPresent':leader}


def growth(a,b):
    return None if a is None or b is None or a==0 else (b/a-1)*100


def load_global_files(hs,flow):
    # Use every existing all-reporter file for the product; concatenate and deduplicate.
    paths=sorted(RAW.glob(f'*ALLREPORTERS_{hs}_{flow}_WORLD.parquet'))
    frames=[]
    for p in paths:
        try:
            d=pd.read_parquet(p)
            if isinstance(d,pd.DataFrame) and not d.empty and {'refYear','reporterCode','primaryValue'}.issubset(d.columns):
                d=d.copy(); d['_source_file']=p.name; frames.append(d)
        except Exception:
            pass
    if not frames:return pd.DataFrame(),[]
    z=pd.concat(frames,ignore_index=True)
    z=base(z)
    if z.empty:return z,[p.name for p in paths]
    # Prefer the maximum value for duplicate reporter/year technical records rather than summing duplicates.
    keys=[c for c in ['refYear','reporterCode'] if c in z.columns]
    z=z.sort_values('primaryValue',ascending=False).drop_duplicates(keys)
    return z,[p.name for p in paths]


def choose_benchmark(gx,gm,max_year=None):
    ex_years=set(pd.to_numeric(gx.get('refYear',pd.Series(dtype=float)),errors='coerce').dropna().astype(int).tolist()) if not gx.empty else set()
    im_years=set(pd.to_numeric(gm.get('refYear',pd.Series(dtype=float)),errors='coerce').dropna().astype(int).tolist()) if not gm.empty else set()
    years=sorted(ex_years & im_years)
    if max_year is not None: years=[y for y in years if y<=max_year]
    audit=[]
    for y in sorted(years,reverse=True):
        if y-1 not in years: continue
        ex=coverage(gx,y,y-1); im=coverage(gm,y,y-1)
        valid=ex['valid'] and im['valid']
        audit.append({'year':y,'valid':valid,'exports':ex,'imports':im})
        if valid:return y,audit
    return None,audit


def withheld(latest,audit,note):
    return {'available':False,'comparisonYear':None,'latestRequestedYear':latest,'reportedWorldExports':None,'reportedWorldImports':None,'worldExportGrowthYoY':None,'indiaExportRank':None,'indiaImportRank':None,'indiaExportShare':None,'indiaImportShare':None,'leader':None,'leaderShare':None,'reporterCount':0,'coverageStatus':'incomplete','coverageNote':note,'coverageAudit':audit,'topExporters':[],'topImporters':[]}


def migrate_one(path):
    d=json.loads(path.read_text())
    hs=str(d.get('product',{}).get('hs6') or path.stem)
    latest=int(d.get('period',{}).get('latest') or d.get('period',{}).get('end') or 2025)
    gx,xfiles=load_global_files(hs,'X'); gm,mfiles=load_global_files(hs,'M')
    bench,audit=choose_benchmark(gx,gm,latest)
    if bench is None:
        g=withheld(latest,audit,'No year in the existing raw files passed reporter-coverage validation. Global total, India share and rank are withheld.')
        status='WITHHELD'; detail='no validated benchmark'
    else:
        rx=ranking(gx,bench); rm=ranking(gm,bench); prev=ranking(gx,bench-1)
        g={'available':True,'comparisonYear':bench,'latestRequestedYear':latest,'reportedWorldExports':rx['total'],'reportedWorldImports':rm['total'],'worldExportGrowthYoY':growth(prev.get('total'),rx['total']),'indiaExportRank':rx['indiaRank'],'indiaImportRank':rm['indiaRank'],'indiaExportShare':rx['indiaShare'],'indiaImportShare':rm['indiaShare'],'leader':rx['leader'],'leaderShare':rx['leaderShare'],'reporterCount':rx['count'],'coverageStatus':'validated','coverageNote':f'Global comparison uses {bench}, the latest year in locally stored Comtrade data passing reporter-coverage checks. India headline trade remains {latest}.','coverageAudit':audit,'topExporters':rx['top'],'topImporters':rm['top']}
        status='VALIDATED'; detail=f'{bench}; {rx["count"]} exporters; world exports ${rx["total"]/1e9:.2f}bn'
    d['global']=g
    d['schemaVersion']='0.5.2-revalidated'
    d.setdefault('quality',{})['globalCoverageStatus']=g['coverageStatus']
    d['quality']['revalidatedOffline']=True
    d.setdefault('provenance',{})['globalRawRevalidation']={'exportFiles':xfiles,'importFiles':mfiles}
    path.write_text(json.dumps(d,indent=2))
    out=PROCESSED/f'{hs}.json'
    if out.parent.exists() or PROCESSED.exists():
        PROCESSED.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(d,indent=2))
    return hs,status,detail


def main():
    rows=[]
    for p in sorted(PUBLIC.glob('*.json')):
        try:rows.append(migrate_one(p))
        except Exception as e: rows.append((p.stem,'ERROR',f'{type(e).__name__}: {e}'))
    counts={k:sum(1 for _,s,_ in rows if s==k) for k in ['VALIDATED','WITHHELD','ERROR']}
    print(f"Offline global revalidation: {counts['VALIDATED']} validated | {counts['WITHHELD']} withheld | {counts['ERROR']} errors")
    for hs,s,msg in rows:
        print(f'  {s:9} {hs}: {msg}')
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps({'summary':counts,'products':[{'hs':h,'status':s,'detail':m} for h,s,m in rows]},indent=2))
    if counts['ERROR']: raise SystemExit(1)

if __name__=='__main__':main()
