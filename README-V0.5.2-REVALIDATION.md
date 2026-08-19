# HStat.India V0.5.2 — Offline Global Revalidation

This patch performs no Comtrade API calls. It revalidates existing product JSON files against all locally stored `ALLREPORTERS` Parquet files, selects the latest global benchmark year that passes reporter-coverage checks, and withholds global metrics where no year passes.

Run:

```bash
./scripts/revalidate-existing.sh
```

The migration report is written to `data/qa/revalidation_report.json`.
