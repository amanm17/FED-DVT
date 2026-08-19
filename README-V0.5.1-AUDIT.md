# HStat.India V0.5.1 — Calculation Audit Patch

This patch hardens the stable V0.5 build without reintroducing the V0.6 multi-year UI.

## Core correction

HStat no longer assumes that the newest UN Comtrade year is a complete global comparison year.

A candidate global benchmark year is accepted only when, versus the previous year:

- the previous-year #1 reporter is present;
- at least 4 of the previous top 5 reporters are present;
- available reporters cover at least 90% of the previous top-20 trade value;
- reporter count is at least 75% of the previous year's count;
- both export and import reporter sets pass these checks.

If a year fails, HStat moves backward. If no recent year passes, global total, rank and share are withheld.

India's own latest-year imports/exports remain independent from the global benchmark year.

## Other checks

- defensive handling of empty/quota API responses;
- one World aggregate row per annual total (largest after technical-filtering, never summing World plus partner rows);
- technical totals filtered to partner2=World, mode of transport=total, customs=total where available;
- reporter rows deduplicated before ranking;
- partner rows deduplicated before concentration calculations;
- global share and rank always use the same benchmark year and denominator;
- top reporter shares always use the same validated reported-world denominator;
- partner-allocation coverage warnings when country/area partners explain <80% or >105% of the reporter's World total;
- build-time `pipeline/sanity_audit.py` for arithmetic/rank/share/HHI consistency.

## Refresh one HS product

```bash
./scripts/refresh-hs.sh 847130 2021 2025
```

The global API call now requests up to the last four years in one call to validate coverage. A 2025 India headline can therefore coexist with a validated 2024 global benchmark.

## Audit all currently loaded product JSON files

```bash
python pipeline/sanity_audit.py
```

The report is written to:

`data/qa/sanity_audit.json`
