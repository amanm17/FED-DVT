#!/usr/bin/env python3
"""HStat.India — UN Comtrade extraction helper.

Uses the official UN Comtrade Python package. This script intentionally writes
raw snapshots first; transformation/loading into D1 is a separate step so every
published figure can be traced to its source snapshot.
"""
from __future__ import annotations
import argparse, json, os
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import comtradeapicall

RAW = Path('data/raw/comtrade')
MANIFESTS = Path('data/manifests')

def fetch(period: str, reporter: str, cmd: str, flow: str, partner: str | None, key: str | None):
    kwargs = dict(
        typeCode='C', freqCode='A', clCode='HS', period=period,
        reporterCode=reporter, cmdCode=cmd, flowCode=flow,
        partnerCode=partner, partner2Code=None, customsCode=None, motCode=None,
        maxRecords=500 if not key else 250000, format_output='JSON',
        aggregateBy=None, breakdownMode='classic', countOnly=None, includeDesc=True,
    )
    return comtradeapicall.getFinalData(key, **kwargs) if key else comtradeapicall.previewFinalData(**kwargs)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--period', default='2025')
    ap.add_argument('--reporter', default='699', help='UN Comtrade reporter code. Verify via official reference table before production runs.')
    ap.add_argument('--cmd', default='847130', help='HS commodity code')
    ap.add_argument('--flow', default='M', choices=['M','X'])
    ap.add_argument('--partner', default=None)
    ap.add_argument('--preview', action='store_true', help='Force keyless preview API (500-record limit).')
    args = ap.parse_args()

    key = None if args.preview else os.environ.get('COMTRADE_API_KEY')
    if not key and not args.preview:
        print('COMTRADE_API_KEY not set; falling back to official preview endpoint.')

    extracted_at = datetime.now(timezone.utc).isoformat()
    df = fetch(args.period, args.reporter, args.cmd, args.flow, args.partner, key)
    RAW.mkdir(parents=True, exist_ok=True); MANIFESTS.mkdir(parents=True, exist_ok=True)
    stem = f"{args.period}_{args.reporter}_{args.cmd}_{args.flow}_{args.partner or 'ALL'}"
    out = RAW / f'{stem}.parquet'
    df.to_parquet(out, index=False)
    manifest = {
        'source':'UN Comtrade API', 'extracted_at':extracted_at,
        'period':args.period, 'reporterCode':args.reporter, 'cmdCode':args.cmd,
        'flowCode':args.flow, 'partnerCode':args.partner, 'classification':'HS',
        'row_count_received':int(len(df)), 'raw_file':str(out),
        'mode':'preview' if not key else 'authenticated', 'processing_version':'0.1.0'
    }
    (MANIFESTS / f'{stem}.json').write_text(json.dumps(manifest, indent=2))
    print(f'Wrote {len(df):,} rows -> {out}')
    print(json.dumps(manifest, indent=2))

if __name__ == '__main__': main()
