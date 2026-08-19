# HStat.India V0.6 — annual reports + QA

Adds full-year global rankings and India partner analytics for every loaded year, a report-year selector, chart axis titles, and automated QA.

## Refresh one HS code

```bash
./scripts/refresh-hs.sh 847130 2020 2025
```

## Refresh the full MeitY universe

```bash
./scripts/preload-meity-universe.sh 2020 2025
```

## Run QA only

```bash
python pipeline/qa_products.py
```

QA outputs:
- `data/qa/qa_report.json`
- `data/qa/qa_report.csv`

A failed invariant exits non-zero. Warnings remain visible in the QA report but do not block the build.
