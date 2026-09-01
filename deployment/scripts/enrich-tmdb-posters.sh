#!/usr/bin/env bash
set -euo pipefail

REPORT_DIR="${WGDB_TMDB_REPORT_DIR:-$HOME/wgdb-tmdb-report}"
ENV_FILE="${WGDB_BACKEND_ENV:-$HOME/.config/wgdb/backend.env}"
IMAGE="${WGDB_BACKEND_IMAGE:-localhost/wgdb-backend:production}"

mkdir -p "$REPORT_DIR"

# Container runs as uid/gid 10001.
podman unshare chown -R 10001:10001 "$REPORT_DIR"

podman run --rm \
  --network wgdb \
  --env-file "$ENV_FILE" \
  -v "$REPORT_DIR:/reports" \
  "$IMAGE" \
  python /app/scripts/enrich_tmdb_posters.py "$@"

echo
echo "TMDB report: $REPORT_DIR"
