#!/usr/bin/env bash
set -uo pipefail
START="${1:-2021}"; END="${2:-2025}"; FAIL=0; DONE=0
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
python pipeline/build_hs_library.py
LIST="config/meity_hs6_all.txt"
TOTAL=$(grep -Ec '^[0-9]{6}$' "$LIST" || true)
echo "HStat MeitY universe preload: $TOTAL HS-6 codes ($START-$END)"
while IFS= read -r HS || [ -n "$HS" ]; do
  [[ "$HS" =~ ^[0-9]{6}$ ]] || continue
  DONE=$((DONE+1))
  echo ""
  echo "[$DONE/$TOTAL] HS $HS"
  # Retry once for transient API/network failures. Continue on failure so the run is resumable.
  if ! python pipeline/refresh_product.py --hs "$HS" --start "$START" --end "$END"; then
    echo "Retrying HS $HS once..."
    sleep 3
    if ! python pipeline/refresh_product.py --hs "$HS" --start "$START" --end "$END"; then
      echo "FAILED HS $HS" >&2
      FAIL=$((FAIL+1))
    fi
  fi
  # Light pacing reduces the chance of throttling on long authenticated runs.
  sleep 1
done < "$LIST"
python pipeline/build_catalogue.py
python pipeline/build_hs_library.py
npm run build
LOADED=$(find public/data/products -maxdepth 1 -name '*.json' | wc -l | tr -d ' ')
echo ""
echo "HStat preload complete: $LOADED product datasets present; $FAIL failures in this run."
if [ "$FAIL" -gt 0 ]; then
  echo "Re-run this same command to retry failed codes; successful files are safe to overwrite."
fi
