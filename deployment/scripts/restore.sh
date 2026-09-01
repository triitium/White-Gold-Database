#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 /path/to/wgdb-YYYYMMDD-HHMMSS.dump" >&2
    exit 2
fi

DUMP="$(realpath "$1")"
[[ -f "$DUMP" ]] || { echo "Backup not found: $DUMP" >&2; exit 1; }

if [[ -f "$DUMP.sha256" ]]; then
    (cd "$(dirname "$DUMP")" && sha256sum --check "$(basename "$DUMP").sha256")
fi

read -r -p "This will replace the current WGDB database. Type RESTORE to continue: " answer
[[ "$answer" == "RESTORE" ]] || { echo "Cancelled."; exit 1; }

systemctl --user stop wgdb-backend.service
trap 'systemctl --user start wgdb-backend.service >/dev/null 2>&1 || true' EXIT

podman exec wgdb-postgres psql --username=wgdb_app --dbname=postgres --set=ON_ERROR_STOP=1 \
    --command="SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='wgdb' AND pid <> pg_backend_pid();"
podman exec wgdb-postgres dropdb --username=wgdb_app --if-exists wgdb
podman exec wgdb-postgres createdb --username=wgdb_app wgdb
cat "$DUMP" | podman exec -i wgdb-postgres \
    pg_restore --username=wgdb_app --dbname=wgdb --no-owner --no-acl --exit-on-error

systemctl --user start wgdb-backend.service
trap - EXIT

echo "Restore completed."
