#!/usr/bin/env bash
set -euo pipefail
LIST="${1:-config/meity_hs6_seed.txt}"; START="${2:-2021}"; END="${3:-2025}"; FAIL=0
[ -f "$LIST" ] || { echo "HS list not found: $LIST" >&2; exit 1; }
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
while IFS= read -r raw || [ -n "$raw" ]; do
 HS="$(printf '%s' "$raw"|sed 's/#.*//'|tr -d '[:space:]')"; [ -z "$HS" ]&&continue
 [[ "$HS" =~ ^[0-9]{6}$ ]] || { echo "Skipping invalid HS-6: $HS";continue; }
 echo "==== Refreshing HS $HS ===="
 python pipeline/refresh_product.py --hs "$HS" --start "$START" --end "$END" || { echo "WARNING: $HS failed";FAIL=$((FAIL+1)); }
done < "$LIST"
python pipeline/build_catalogue.py
python pipeline/build_hs_library.py
npm run build
echo "Batch complete. Failed products: $FAIL"
