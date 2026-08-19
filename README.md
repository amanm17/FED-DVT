# HStat.India

Global-to-India electronics trade intelligence for MeitY-oriented analysis.

## V0.1 scope
- World-first overview.
- Product search by product name, HS-6 and India ITC(HS)-8.
- HS-6 product intelligence page.
- India always visible in the global context.
- India-specific 8-digit drill-down.
- Supplier and destination concentration.
- Upstream/downstream curated supply-chain context.
- D1-ready schema and R2-ready raw-data architecture.
- UN Comtrade extraction script using the official Python package.

**Important:** the UI currently contains clearly labelled synthetic demonstration values. They exist only to validate interaction and visual hierarchy. Do not use them as trade statistics.

## 1. Run the interface locally

```bash
cd HStat.India
npm install
npm run dev
```

Vite will print the local address, normally `http://localhost:5173`.

## 2. Test the Cloudflare Worker build locally

```bash
npm run build
npx wrangler dev
```

Check:

```bash
curl http://localhost:8787/api/health
```

## 3. Set up UN Comtrade extraction

UN Comtrade's official `comtradeapicall` package is used rather than maintaining a hand-written API wrapper.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Keyless preview test:

```bash
python pipeline/ingest_comtrade.py --preview --period 2025 --cmd 847130 --flow M
```

For authenticated extraction, first place the API key in the shell (never commit it):

```bash
export COMTRADE_API_KEY='YOUR_KEY_HERE'
python pipeline/ingest_comtrade.py --period 2025 --cmd 847130 --flow M
```

The script writes immutable snapshots to `data/raw/comtrade/` and a provenance manifest to `data/manifests/`.

## 4. Create Cloudflare storage when ready

Login:

```bash
npx wrangler login
```

Create D1:

```bash
npx wrangler d1 create hstat-india
```

Create R2:

```bash
npx wrangler r2 bucket create hstat-india-raw
```

Copy the D1 database ID returned by Wrangler into `wrangler.jsonc`, using `wrangler.resources.example.jsonc` as the binding template. Add the R2 binding and the weekly cron only after the resources exist.

Initialise D1:

```bash
npx wrangler d1 execute hstat-india --remote --file=database/schema.sql
npx wrangler d1 execute hstat-india --remote --file=database/seed.sql
```

Store the Comtrade key in Cloudflare:

```bash
npx wrangler secret put COMTRADE_API_KEY
```

## 5. Deploy

```bash
npm run deploy
```

Cloudflare will return the Worker URL.

## 6. GitHub

```bash
git init
git add .
git commit -m "Initial HStat.India prototype"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

`node_modules`, build output and environment/secrets are excluded by `.gitignore`.

## Architecture

```text
UN Comtrade ─┐
             ├─> extraction + manifests ─> raw archive (R2)
India ITC(HS)┘                              │
                                            v
                                  validation / transforms
                                            │
                                            v
                                   analytics tables (D1)
                                            │
                                            v
                                     Worker API
                                            │
                                            v
                                     React interface
```

GitHub contains application code, schema, methodology, mappings and reproducible processing logic — not the primary trade warehouse.

## Immediate next implementation milestone
1. Validate the MeitY product universe and HS-6 list.
2. Load current official HS descriptions and country reference tables.
3. Establish the authoritative India 8-digit data acquisition route.
4. Replace synthetic UI fixtures with validated source data.
5. Add derived indicators and deterministic policy-insight rules.
