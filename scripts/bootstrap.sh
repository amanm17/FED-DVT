#!/usr/bin/env bash
set -euo pipefail
printf '\nHStat.India bootstrap\n=====================\n'
command -v node >/dev/null || { echo 'Node.js is required.'; exit 1; }
command -v npm >/dev/null || { echo 'npm is required.'; exit 1; }
echo "Node: $(node --version)"
echo "npm:  $(npm --version)"
npm install
npm run build
printf '\nBuild successful. Start the UI with:\n  npm run dev\n\nCloudflare-integrated local run:\n  npx wrangler dev\n'
