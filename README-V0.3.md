# HStat.India V0.3 — catalogue-driven real data

This patch generalises V0.2 from one product to any HS-6 product successfully generated through the authenticated UN Comtrade pipeline.

## One product

```bash
./scripts/refresh-hs.sh 847130 2021 2025
```

## Batch

Edit `config/meity_hs6_seed.txt`, then run:

```bash
./scripts/refresh-batch.sh config/meity_hs6_seed.txt 2021 2025
```

The UI search indexes `public/data/catalogue.json`, which is rebuilt from actual generated product JSON files. No catalogue entry is created unless a real HStat product snapshot exists.

## Important

- HS-6 is the global comparison layer.
- India ITC(HS)-8 remains intentionally unavailable until the authoritative India-specific layer is integrated.
- Upstream/downstream relationships remain separate curated evidence, not inferred from Comtrade.
