#!/usr/bin/env bash
set -euo pipefail

CONFIG_DIR="${WGDB_CONFIG_DIR:-$HOME/.config/wgdb}"

podman run --rm -it \
    --network wgdb \
    --env-file "$CONFIG_DIR/backend.env" \
    localhost/wgdb-backend:production \
    python -m app.cli.create_admin
