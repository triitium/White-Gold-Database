#!/usr/bin/env bash
set -euo pipefail

CONFIG_DIR="${WGDB_CONFIG_DIR:-$HOME/.config/wgdb}"

systemctl --user start wgdb-network-network.service wgdb-postgres-volume.service wgdb-postgres.service

healthy=0
for _ in $(seq 1 60); do
    if podman healthcheck run wgdb-postgres >/dev/null 2>&1; then
        healthy=1
        break
    fi
    sleep 2
done

if [[ "$healthy" -ne 1 ]]; then
    echo "PostgreSQL did not become healthy within 120 seconds" >&2
    exit 1
fi

podman run --rm \
    --network wgdb \
    --env-file "$CONFIG_DIR/backend.env" \
    localhost/wgdb-backend:production \
    alembic upgrade head
