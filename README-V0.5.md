# HStat.India V0.5 — Full MeitY universe preload

This patch:

- fixes the Recharts TypeScript tooltip formatter build error;
- removes the terminal-command message from the user-facing missing-data state;
- generates the complete HS-6 leaf-code list beneath the configured MeitY headings;
- preloads every HS-6 code beneath 8471, 8473, 8507, 8517, 8541 and 8542;
- retries failed API calls once and allows a full preload to be rerun safely;
- improves India tariff-line retrieval by requesting all partners and falling back from annual to monthly tariff-line data before aggregating to ITC/HS-8;
- rebuilds the catalogue/search library and production frontend after preload.

Run:

```bash
./scripts/preload-meity-universe.sh 2021 2025
```

The generated scope list is stored at `config/meity_hs6_all.txt`.

Search at HS-2 and HS-4 remains hierarchical discovery. Product analytics are at HS-6 globally, with India tariff-line detail at 8 digits when published in the source data.
