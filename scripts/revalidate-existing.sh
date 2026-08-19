#!/usr/bin/env bash
set -euo pipefail
python pipeline/revalidate_existing_products.py
python pipeline/build_catalogue.py
python pipeline/sanity_audit.py
npm run build
