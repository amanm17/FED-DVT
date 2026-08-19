#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os
from datetime import datetime,timezone
from pathlib import Path
import comtradeapicall,pandas as pd
from dotenv import load_dotenv
load_dotenv()
RAW=Path('data/raw/comtrade'); PROCESSED=Path('data/processed'); PUBLIC=Path('public/data/products'); MANIFESTS=Path('data/manifests')
REQ={'refYear','reporterCode','primaryValue'}

def _ensure_df(df,label,required=None):
    if df is None or not isinstance(df,pd.DataFrame): raise RuntimeError(f'{label}: Comtrade returned no table (quota/throttle/unavailable).')
    required=set(required or [])
    missing=required-set(df.columns)
    if missing: raise RuntimeError(f'{label}: response missing required fields: {sorted(missing)}')
    return df

def final(key,periods,reporter,hs,flow,partner):
    d=comtradeapicall.getFinalData(key,typeCode='C',freqCode='A',clCode='HS',period=periods,reporterCode=reporter,cmdCode=hs,flowCode=flow,partnerCode=partner,partner2Code=None,customsCode=None,motCode=None,maxRecords=250000,format_output='JSON',aggregateBy=None,breakdownMode='classic',countOnly=None,includeDesc=True)
    return _ensure_df(d,f'Final data {flow} {hs}',{'refYear','reporterCode','primaryValue'})

def tariff(key,period,reporter,hs,flow):
    d=comtradeapicall.getTarifflineData(key,typeCode='C',freqCode='A',clCode='HS',period=str(period),reporterCode=reporter,cmdCode=hs,flowCode=flow,partnerCode=None,partner2Code=None,customsCode=None,motCode=None,maxRecords=250000,format_output='JSON',countOnly=None,includeDesc=True)
    if isinstance(d,pd.DataFrame) and not d.empty:return d
    months=','.join(f'{period}{m:02d}' for m in range(1,13))
    d=comtradeapicall.getTarifflineData(key,typeCode='C',freqCode='M',clCode='HS',period=months,reporterCode=reporter,cmdCode=hs,flowCode=flow,partnerCode=None,partner2Code=None,customsCode=None,motCode=None,maxRecords=250000,format_output='JSON',countOnly=None,includeDesc=True)
    return d if isinstance(d,pd.DataFrame) else pd.DataFrame()

def write_raw(df,stem):
    _ensure_df(df,stem); RAW.mkdir(parents=True,exist_ok=True);p=RAW/f'{stem}.parquet';df.to_parquet(p,index=False);return str(p)

def _base(df):
    if df.empty:return df.copy()
    z=df.copy()
    for c,v in [('partner2Code',0),('motCode',0)]:
        if c in z.columns:z=z[z[c].fillna(v).astype(str)==str(v)]
    if 'customsCode' in z.columns and (z['customsCode'].astype(str)=='C00').any():z=z[z['customsCode'].astype(str)=='C00']
    z['primaryValue']=pd.to_numeric(z['primaryValue'],errors='coerce')
    return z

def world_rows(df):
    z=_base(df)
    return z[z['partnerCode'].astype(str)=='0'].copy() if 'partnerCode' in z.columns else z

def annual_totals(df):
    out={}
    z=world_rows(df)
    for y,g in z.groupby('refYear'):
        vals=g['primaryValue'].dropna()
        if len(vals): out[int(y)]=float(vals.max())
    return out

def partner_rows(df,year):
    z=_base(df)
    if z.empty:return z
    z=z[(z['refYear']==year)&(z['partnerCode'].astype(str)!='0')].copy()
    # one row per partner; if duplicate technical rows remain, keep the largest total rather than double count
    z=z.sort_values('primaryValue',ascending=False).drop_duplicates('partnerCode')
    return z

def partners(df,total,n=10):
    if total<=0 or df.empty:return []
    out=[]
    for _,r in df.head(n).iterrows():
        v=float(r.get('primaryValue') or 0)
        out.append({'code':int(r['partnerCode']),'iso':None if pd.isna(r.get('partnerISO')) else str(r.get('partnerISO')),'name':str(r.get('partnerDesc')),'value':v,'share':v/total*100,'quantity':None if pd.isna(r.get('qty')) else float(r.get('qty')),'quantityUnit':None if pd.isna(r.get('qtyUnitAbbr')) else str(r.get('qtyUnitAbbr')),'netWeightKg':None if pd.isna(r.get('netWgt')) else float(r.get('netWgt')),'quantityEstimated':bool(r.get('isQtyEstimated',False)),'netWeightEstimated':bool(r.get('isNetWgtEstimated',False))})
    return out

def growth(a,b): return None if a is None or b is None or a==0 else (b/a-1)*100

def cagr(a,b,n): return None if a is None or b is None or a<=0 or b<0 or n<=0 else ((b/a)**(1/n)-1)*100

def conc(df,total):
    if total<=0 or df.empty:return {'largestShare':None,'top3Share':None,'hhi':None,'level':None,'partnerCoverage':None}
    s=df['primaryValue'].fillna(0).astype(float)/total;h=float((s**2).sum());cov=float(s.sum()*100)
    return {'largestShare':float(s.iloc[0]*100),'top3Share':float(s.head(3).sum()*100),'hhi':h,'level':'High' if h>=.25 else 'Moderate' if h>=.15 else 'Low','partnerCoverage':cov}

def is_reporting_economy(r):
    iso=str(r.get('reporterISO',''))
    return len(iso)==3 and iso.isalpha() and iso!='WLD'

def reporter_frame(df,year):
    if df is None or df.empty:return pd.DataFrame(columns=['reporterCode','reporterDesc','reporterISO','primaryValue'])
    z=_base(df); z=z[z['refYear']==year].copy(); z=z[z.apply(is_reporting_economy,axis=1)]
    if z.empty:return z
    z=z[z['primaryValue'].fillna(-1)>=0].sort_values('primaryValue',ascending=False).drop_duplicates('reporterCode').reset_index(drop=True)
    return z

def ranking(df,year,india_reporter):
    cur=reporter_frame(df,year)
    if cur.empty:return {'total':None,'indiaRank':None,'indiaShare':None,'leader':None,'leaderShare':None,'count':0,'top':[]}
    total=float(cur['primaryValue'].fillna(0).sum()); india=cur[cur['reporterCode'].astype(str)==str(india_reporter)]; iv=float(india.iloc[0]['primaryValue']) if not india.empty else None
    rank=int((cur['primaryValue'].astype(float)>iv).sum()+1) if iv is not None else None
    top=[]
    for idx,r in cur.head(10).iterrows():
        v=float(r['primaryValue'] or 0);top.append({'code':int(r['reporterCode']),'iso':None if pd.isna(r.get('reporterISO')) else str(r.get('reporterISO')),'name':str(r.get('reporterDesc')),'value':v,'share':v/total*100 if total else 0,'rank':idx+1})
    leader=top[0] if top else None
    return {'total':total,'indiaRank':rank,'indiaShare':iv/total*100 if iv is not None and total else None,'leader':leader['name'] if leader else None,'leaderShare':leader['share'] if leader else None,'count':len(cur),'top':top}

def coverage(df,year,prev_year,top_n=20):
    cur=reporter_frame(df,year); prev=reporter_frame(df,prev_year)
    if cur.empty or prev.empty:return {'valid':False,'reason':'Insufficient adjacent-year reporter data','reporterCount':len(cur),'previousReporterCount':len(prev),'reporterCountRatio':None,'top5Present':0,'weightedTop20Coverage':None,'previousLeaderPresent':False}
    prev_map=dict(zip(prev['reporterCode'].astype(str),prev['primaryValue'].astype(float)))
    cur_codes=set(cur['reporterCode'].astype(str))
    top=prev.head(top_n); denom=float(top['primaryValue'].sum())
    weighted=float(top[top['reporterCode'].astype(str).isin(cur_codes)]['primaryValue'].sum()/denom) if denom>0 else 0.0
    top5=prev.head(5); top5_present=int(top5['reporterCode'].astype(str).isin(cur_codes).sum())
    leader=str(prev.iloc[0]['reporterCode']) in cur_codes
    ratio=len(cur)/len(prev) if len(prev) else None
    valid=bool(leader and top5_present>=4 and weighted>=0.90 and ratio is not None and ratio>=0.75)
    reasons=[]
    if not leader:reasons.append(f'previous-year leader {prev.iloc[0].get("reporterDesc")} missing')
    if top5_present<4:reasons.append(f'only {top5_present}/5 prior top exporters/importers present')
    if weighted<0.90:reasons.append(f'prior top-{top_n} value coverage {weighted:.1%}')
    if ratio is None or ratio<0.75:reasons.append(f'reporter-count ratio {ratio:.1%}' if ratio is not None else 'reporter-count ratio unavailable')
    return {'valid':valid,'reason':'; '.join(reasons) if reasons else 'Coverage checks passed','reporterCount':len(cur),'previousReporterCount':len(prev),'reporterCountRatio':ratio,'top5Present':top5_present,'weightedTop20Coverage':weighted,'previousLeaderPresent':leader}

def choose_benchmark(gx,gm,years):
    audit=[]
    for y in sorted(years,reverse=True):
        if y-1 not in years:continue
        ex=coverage(gx,y,y-1); im=coverage(gm,y,y-1)
        valid=ex['valid'] and im['valid']
        audit.append({'year':y,'valid':valid,'exports':ex,'imports':im})
        if valid:return y,audit
    return None,audit

def tariff_lines(imp,exp,hs):
    def clean(df):
        if df is None or df.empty:return {}
        z=df.copy();z['_code']=z['cmdCode'].astype(str).str.replace(r'\D','',regex=True);z=z[(z['_code'].str.len()>=8)&(z['_code'].str.startswith(hs))]
        if z.empty:return {}
        out={}
        for code,g in z.groupby('_code'):
            world=g[g['partnerCode'].astype(str)=='0'] if 'partnerCode' in g.columns else g.iloc[0:0];use=world if not world.empty else g[g['partnerCode'].astype(str)!='0'] if 'partnerCode' in g.columns else g
            value=float(pd.to_numeric(use['primaryValue'],errors='coerce').fillna(0).sum());qty=float(pd.to_numeric(use['qty'],errors='coerce').fillna(0).sum()) if 'qty' in use.columns else 0.0;desc=str(g.iloc[0].get('cmdDesc','')).strip();unit=None
            if 'qtyUnitAbbr' in g.columns:
                units=[str(x) for x in g['qtyUnitAbbr'].dropna().unique() if str(x)];unit=units[0] if len(units)==1 else None
            out[code]={'description':desc,'value':value,'qty':qty,'unit':unit}
        return out
    I,E=clean(imp),clean(exp);out=[]
    for code in sorted(set(I)|set(E)):
        a,b=I.get(code,{}),E.get(code,{});iv=float(a.get('value',0) or 0);ev=float(b.get('value',0) or 0)
        out.append({'code':code,'description':a.get('description') or b.get('description') or code,'imports':iv,'exports':ev,'tradeBalance':ev-iv,'quantity':a.get('qty') if a else b.get('qty'),'quantityUnit':a.get('unit') if a else b.get('unit')})
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--hs',default='847130');ap.add_argument('--start',type=int,default=2021);ap.add_argument('--end',type=int,default=2025);ap.add_argument('--india-reporter',default='699');ap.add_argument('--skip-global',action='store_true');ap.add_argument('--skip-india8',action='store_true');a=ap.parse_args()
    key=os.getenv('COMTRADE_API_KEY')
    if not key:raise SystemExit('COMTRADE_API_KEY is missing.')
    years=list(range(a.start,a.end+1));periods=','.join(map(str,years));now=datetime.now(timezone.utc).isoformat()
    print(f'Fetching India imports for HS {a.hs}, {a.start}-{a.end} …');imp=final(key,periods,a.india_reporter,a.hs,'M',None);ifile=write_raw(imp,f'{a.start}-{a.end}_{a.india_reporter}_{a.hs}_M_ALL')
    print(f'Fetching India exports for HS {a.hs}, {a.start}-{a.end} …');exp=final(key,periods,a.india_reporter,a.hs,'X',None);efile=write_raw(exp,f'{a.start}-{a.end}_{a.india_reporter}_{a.hs}_X_ALL')
    it,et=annual_totals(imp),annual_totals(exp);latest=a.end;li=it.get(latest,0.0);le=et.get(latest,0.0);sdf=partner_rows(imp,latest);ddf=partner_rows(exp,latest);sl=partners(sdf,li);dl=partners(ddf,le)
    cand=world_rows(imp);prow=cand.iloc[-1] if not cand.empty else world_rows(exp).iloc[-1]
    trend=[{'year':y,'indiaImports':it.get(y),'indiaExports':et.get(y),'reportedWorldExports':None} for y in years]
    global_block={'available':False,'comparisonYear':None,'latestRequestedYear':a.end,'reportedWorldExports':None,'reportedWorldImports':None,'worldExportGrowthYoY':None,'indiaExportRank':None,'indiaImportRank':None,'indiaExportShare':None,'indiaImportShare':None,'leader':None,'leaderShare':None,'reporterCount':0,'coverageStatus':'unavailable','coverageNote':'Global comparison not validated.','coverageAudit':[],'topExporters':[],'topImporters':[]};gfiles=[]
    if not a.skip_global:
        try:
            # Fetch at least 4 adjacent years in one call so latest-year completeness can be tested against prior major reporters.
            gstart=max(a.start,a.end-3); gp=','.join(map(str,range(gstart,a.end+1)))
            print(f'Fetching all-reporter exports to World for HS {a.hs}, {gp} …');gx=final(key,gp,None,a.hs,'X','0');gfiles.append(write_raw(gx,f'{gstart}-{a.end}_ALLREPORTERS_{a.hs}_X_WORLD'))
            print(f'Fetching all-reporter imports from World for HS {a.hs}, {gp} …');gm=final(key,gp,None,a.hs,'M','0');gfiles.append(write_raw(gm,f'{gstart}-{a.end}_ALLREPORTERS_{a.hs}_M_WORLD'))
            gy=list(range(gstart,a.end+1)); bench,audit=choose_benchmark(gx,gm,gy)
            if bench is not None:
                rx=ranking(gx,bench,a.india_reporter);rm=ranking(gm,bench,a.india_reporter);prev=ranking(gx,bench-1,a.india_reporter)
                global_block={'available':True,'comparisonYear':bench,'latestRequestedYear':a.end,'reportedWorldExports':rx['total'],'reportedWorldImports':rm['total'],'worldExportGrowthYoY':growth(prev.get('total'),rx['total']),'indiaExportRank':rx['indiaRank'],'indiaImportRank':rm['indiaRank'],'indiaExportShare':rx['indiaShare'],'indiaImportShare':rm['indiaShare'],'leader':rx['leader'],'leaderShare':rx['leaderShare'],'reporterCount':rx['count'],'coverageStatus':'validated','coverageNote':f'Global comparison uses {bench}, the latest year passing reporter-coverage checks. India headline trade remains {a.end}.','coverageAudit':audit,'topExporters':rx['top'],'topImporters':rm['top']}
                for t in trend:
                    y=t['year']
                    if y>=gstart+1:
                        cex=coverage(gx,y,y-1); cim=coverage(gm,y,y-1)
                        if cex['valid'] and cim['valid']:t['reportedWorldExports']=ranking(gx,y,a.india_reporter)['total']
            else:
                global_block['coverageStatus']='incomplete';global_block['coverageAudit']=audit;global_block['coverageNote']='No recent year passed global reporter-coverage checks. World total, India global share and rank are withheld.'
        except Exception as e:
            global_block['coverageStatus']='error';global_block['coverageNote']=f'Global comparison unavailable: {type(e).__name__}: {e}';print(f'WARNING global ranking unavailable: {type(e).__name__}: {e}')
    india8={'available':False,'lines':[],'note':'India 8-digit tariff-line data was not retrieved.'}
    if not a.skip_india8:
        try:
            print(f'Fetching India tariff-line imports for HS {a.hs}, {a.end} …');ti=tariff(key,a.end,a.india_reporter,a.hs,'M');
            if isinstance(ti,pd.DataFrame) and not ti.empty:write_raw(ti,f'{a.end}_{a.india_reporter}_{a.hs}_TARIFF_M_ALL')
            print(f'Fetching India tariff-line exports for HS {a.hs}, {a.end} …');te=tariff(key,a.end,a.india_reporter,a.hs,'X');
            if isinstance(te,pd.DataFrame) and not te.empty:write_raw(te,f'{a.end}_{a.india_reporter}_{a.hs}_TARIFF_X_ALL')
            lines=tariff_lines(ti,te,a.hs);india8={'available':bool(lines),'lines':lines,'note':f'India tariff-line records returned by UN Comtrade for {a.end}.' if lines else 'No usable India 8-digit tariff-line records returned; use DGFT/TradeStat for authoritative ITC(HS)-8 detail.'}
        except Exception as e:india8={'available':False,'lines':[],'note':f'India 8-digit data unavailable in this run: {type(e).__name__}.'};print(f'WARNING India-8 unavailable: {e}')
    sc={};sp=Path('reference/supply_chain.json')
    if sp.exists():
        try:sc=json.loads(sp.read_text()).get(a.hs,{})
        except Exception:sc={}
    supplier_conc=conc(sdf,li);dest_conc=conc(ddf,le)
    # Sanity flags for India partner allocations. Partner totals need not equal World exactly because of unspecified/confidential trade.
    sanity=[]
    for label,c in [('supplier',supplier_conc),('destination',dest_conc)]:
        cov=c.get('partnerCoverage')
        if cov is not None and (cov<80 or cov>105): sanity.append(f'{label} partner allocation covers {cov:.1f}% of World total; concentration metrics should be interpreted cautiously.')
    result={'schemaVersion':'0.5.1-audit','generatedAt':now,'source':'UN Comtrade','product':{'hs6':str(a.hs),'description':str(prow.get('cmdDesc','')),'classification':str(prow.get('classificationCode','HS')),'level':int(prow.get('aggrLevel',6))},'period':{'start':a.start,'end':a.end,'latest':latest},'global':global_block,'india':{'reporterCode':int(a.india_reporter),'imports':li,'exports':le,'tradeBalance':le-li,'importGrowthYoY':growth(it.get(latest-1),li),'exportGrowthYoY':growth(et.get(latest-1),le),'importCAGR':cagr(it.get(a.start),li,latest-a.start),'exportCAGR':cagr(et.get(a.start),le,latest-a.start),'largestSupplier':sl[0] if sl else None,'largestDestination':dl[0] if dl else None,'supplierConcentration':supplier_conc,'exportMarketConcentration':dest_conc},'trend':trend,'suppliers':sl,'destinations':dl,'india8':india8,'supplyChain':{'available':bool(sc),'upstream':sc.get('upstream',[]),'downstream':sc.get('downstream',[]),'context':sc.get('context'),'note':'Curated product relationship layer; not an observed physical transformation flow.'},'quality':{'sanityWarnings':sanity,'globalCoverageStatus':global_block['coverageStatus']},'provenance':{'indiaImportsRaw':ifile,'indiaExportsRaw':efile,'globalRaw':gfiles,'classificationNote':'HS-6 global comparisons may include converted data where reporters use different HS editions; interpret long time series with classification-continuity caution.'}}
    PROCESSED.mkdir(parents=True,exist_ok=True);PUBLIC.mkdir(parents=True,exist_ok=True);(PROCESSED/f'{a.hs}.json').write_text(json.dumps(result,indent=2));(PUBLIC/f'{a.hs}.json').write_text(json.dumps(result,indent=2))
    print('\nHStat product snapshot ready');print(f'  HS: {a.hs}');print(f'  India imports ({latest}): ${li/1e9:.3f}bn');print(f'  India exports ({latest}): ${le/1e9:.3f}bn');print(f'  Global benchmark: {global_block.get("comparisonYear") or "withheld"} ({global_block.get("coverageStatus")})');print(f'  India export rank: {"#"+str(global_block["indiaExportRank"]) if global_block.get("indiaExportRank") else "withheld"}');print(f'  Frontend data: public/data/products/{a.hs}.json')

if __name__=='__main__':main()
