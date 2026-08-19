#!/usr/bin/env bash
set -euo pipefail
python pipeline/build_hs_library.py
python pipeline/build_catalogue.py
npm run build
