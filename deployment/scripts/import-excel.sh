#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 /path/FILME-V1.1.xlsm [importer options, e.g. --commit]" >&2
    exit 2
fi

XLSM="$(realpath "$1")"
shift
[[ -f "$XLSM" ]] || { echo "Workbook not found: $XLSM" >&2; exit 1; }

CONFIG_DIR="${WGDB_CONFIG_DIR:-$HOME/.config/wgdb}"
REPORT_DIR="${WGDB_IMPORT_REPORT_DIR:-$HOME/wgdb-import-report}"
mkdir -p "$REPORT_DIR"

args=(
  podman run --rm
  --network wgdb
  --env-file "$CONFIG_DIR/backend.env"
  --volume "$XLSM:/import/FILME-V1.1.xlsm:ro,Z"
  --volume "$REPORT_DIR:/reports:Z"
)

if [[ -n "${WGDB_IMPORT_OVERRIDES:-}" ]]; then
    OVERRIDES="$(realpath "$WGDB_IMPORT_OVERRIDES")"
    args+=(--volume "$OVERRIDES:/import/overrides.json:ro,Z")
    extra_overrides=(--overrides /import/overrides.json)
else
    extra_overrides=()
fi

"${args[@]}" localhost/wgdb-backend:production \
    python scripts/import_excel.py /import/FILME-V1.1.xlsm \
    --report-dir /reports \
    "${extra_overrides[@]}" "$@"

echo "Import report: $REPORT_DIR"
