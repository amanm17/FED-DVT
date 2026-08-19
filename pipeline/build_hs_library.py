#!/usr/bin/env python3
import json,re
from datetime import datetime,timezone
from pathlib import Path
import comtradeapicall

HEADINGS=[x.strip() for x in Path('config/meity_headings.txt').read_text().splitlines() if x.strip() and not x.startswith('#')]
TAGS=json.loads(Path('reference/search_tags.json').read_text())
OUT=Path('public/data/hs-library.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
ALL6=Path('config/meity_hs6_all.txt')
loaded={p.stem for p in Path('public/data/products').glob('*.json')} if Path('public/data/products').exists() else set()

def pick_col(cols,opts):
    lower={c.lower():c for c in cols}
    for o in opts:
        if o.lower() in lower:return lower[o.lower()]
    for c in cols:
        if any(o.lower() in c.lower() for o in opts):return c
    return None

refs=comtradeapicall.getReference('cmd:H6')
codecol=pick_col(list(refs.columns),['id','code','cmdCode'])
desccol=pick_col(list(refs.columns),['text','description','cmdDesc'])
if not codecol or not desccol: raise SystemExit(f'Could not identify code/description columns: {list(refs.columns)}')
rows=[];seen=set()
for _,r in refs.iterrows():
    code=re.sub(r'\D','',str(r[codecol]))
    if len(code) not in (2,4,6): continue
    # Keep chapters 84/85 only where they are parents of the requested headings,
    # and all 4/6-digit codes beneath the requested headings.
    relevant=(len(code)==2 and any(h.startswith(code) for h in HEADINGS)) or (len(code)>=4 and any(code.startswith(h) or h.startswith(code) for h in HEADINGS))
    if not relevant or code in seen: continue
    seen.add(code)
    parent=None if len(code)==2 else code[:2] if len(code)==4 else code[:4]
    inherited=[]
    for k,v in TAGS.items():
        if code.startswith(k) or k.startswith(code): inherited.extend(v)
    desc=str(r[desccol]).strip()
    tokens=[t.lower() for t in re.findall(r'[A-Za-z][A-Za-z0-9-]{2,}',desc) if len(t)>2][:16]
    rows.append({'code':code,'level':len(code),'description':desc,'parent':parent,'tags':sorted(set(inherited+tokens)),'loaded':code in loaded})
for h in HEADINGS:
    if h not in seen:
        child=next((x for x in rows if x['code'].startswith(h)),None)
        rows.append({'code':h,'level':4,'description':child['description'] if child else f'HS heading {h}','parent':h[:2],'tags':TAGS.get(h,[]),'loaded':False})
rows.sort(key=lambda x:(x['code'],x['level']))
OUT.write_text(json.dumps({'generatedAt':datetime.now(timezone.utc).isoformat(),'scopeHeadings':HEADINGS,'items':rows},indent=2))
leaf6=sorted(x['code'] for x in rows if x['level']==6)
ALL6.write_text('\n'.join(leaf6)+'\n')
print(f'Wrote {len(rows)} searchable HS-2/4/6 records -> {OUT}')
print(f'Wrote {len(leaf6)} MeitY HS-6 leaf codes -> {ALL6}')
