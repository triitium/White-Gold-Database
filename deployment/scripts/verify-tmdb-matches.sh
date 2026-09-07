#!/usr/bin/env bash
set -euo pipefail

IMAGE="${WGDB_BACKEND_IMAGE:-localhost/wgdb-backend:production}"
REPORT_DIR="${WGDB_TMDB_VERIFY_REPORT_DIR:-$HOME/wgdb-tmdb-verify-report}"

mkdir -p "$REPORT_DIR"

podman run --rm \
  --userns=keep-id \
  --user "$(id -u):$(id -g)" \
  --network wgdb \
  --env-file "$HOME/.config/wgdb/backend.env" \
  -v "$REPORT_DIR:/report:Z" \
  "$IMAGE" \
  python /app/scripts/verify_tmdb_matches.py "$@"
