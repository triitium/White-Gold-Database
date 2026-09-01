#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$REPO_DIR"

echo "1/5 Build updated images"
"$REPO_DIR/deployment/scripts/build.sh"

echo "2/5 Apply DB migrations"
"$REPO_DIR/deployment/scripts/migrate.sh"

echo "3/5 Restart backend"
systemctl --user restart wgdb-backend.service

echo "4/5 Restart frontend"
systemctl --user restart wgdb-frontend.service

echo "5/5 Health check"
curl --fail --silent --show-error http://127.0.0.1:18000/health
curl --fail --silent --show-error http://127.0.0.1:18080/healthz
printf '\nWGDB update complete.\n'
