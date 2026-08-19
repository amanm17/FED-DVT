#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path
P=Path('public/data/products'); OUT=Path('public/data/catalogue.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
items=[]
for f in sorted(P.glob('*.json')) if P.exists() else []:
    try:d=json.loads(f.read_text())
    except Exception:continue
    i=d.get('india',{}); g=d.get('global',{}); ls=i.get('largestSupplier') or {}; sc=i.get('supplierConcentration') or {}
    items.append({'hs6':d.get('product',{}).get('hs6',f.stem),'description':d.get('product',{}).get('description'),'classification':d.get('product',{}).get('classification'),'latest':d.get('period',{}).get('latest'),'globalBenchmarkYear':g.get('comparisonYear'),'globalCoverageStatus':g.get('coverageStatus'),'indiaImports':i.get('imports'),'indiaExports':i.get('exports'),'indiaExportRank':g.get('indiaExportRank') if g.get('available') else None,'indiaExportShare':g.get('indiaExportShare') if g.get('available') else None,'largestSupplier':ls.get('name'),'largestSupplierShare':ls.get('share'),'supplierConcentration':sc.get('level'),'exportGrowthYoY':i.get('exportGrowthYoY'),'generatedAt':d.get('generatedAt'),'path':f'/data/products/{f.name}'})
OUT.write_text(json.dumps({'schemaVersion':'0.5.1-audit','generatedAt':datetime.now(timezone.utc).isoformat(),'count':len(items),'products':items},indent=2));print(f'Catalogue: {len(items)} products -> {OUT}')
