#!/usr/bin/env bash
set -euo pipefail
HS="${1:-847130}"; START="${2:-2021}"; END="${3:-2025}"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
python pipeline/refresh_product.py --hs "$HS" --start "$START" --end "$END"
python pipeline/build_catalogue.py
python pipeline/build_hs_library.py
python pipeline/sanity_audit.py
npm run build
echo "Done. Run: npm run dev"
