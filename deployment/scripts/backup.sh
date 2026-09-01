#!/usr/bin/env bash
set -euo pipefail
umask 077

BACKUP_DIR="${WGDB_BACKUP_DIR:-$HOME/backups/wgdb}"
RETENTION_DAYS="${WGDB_BACKUP_RETENTION_DAYS:-30}"
STAMP="$(date +'%Y%m%d-%H%M%S')"
OUT="$BACKUP_DIR/wgdb-$STAMP.dump"

mkdir -p "$BACKUP_DIR"

if ! podman container exists wgdb-postgres; then
    echo "wgdb-postgres container does not exist" >&2
    exit 1
fi

podman exec wgdb-postgres \
    pg_dump --username=wgdb_app --dbname=wgdb --format=custom --no-owner --no-acl \
    > "$OUT"

sha256sum "$OUT" > "$OUT.sha256"
find "$BACKUP_DIR" -type f \( -name 'wgdb-*.dump' -o -name 'wgdb-*.dump.sha256' \) -mtime "+$RETENTION_DAYS" -delete

echo "Created $OUT"
