#!/usr/bin/env bash
set -euo pipefail
SERVICE="${1:-backend}"
case "$SERVICE" in
  backend|frontend|postgres) ;;
  *) echo "Usage: $0 [backend|frontend|postgres]" >&2; exit 2 ;;
esac
journalctl --user -u "wgdb-${SERVICE}.service" -f
