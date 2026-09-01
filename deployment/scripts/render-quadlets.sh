#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
CONFIG_DIR="${2:-$HOME/.config/wgdb}"
SOURCE_DIR="$REPO_DIR/deployment/quadlet"
TARGET_DIR="$HOME/.config/containers/systemd"

mkdir -p "$TARGET_DIR" "$CONFIG_DIR"

render() {
    local src="$1"
    local dst="$2"
    sed \
        -e "s|@@WGDB_REPO@@|$REPO_DIR|g" \
        -e "s|@@WGDB_CONFIG@@|$CONFIG_DIR|g" \
        "$src" > "$dst"
}

cp "$SOURCE_DIR/wgdb-network.network" "$TARGET_DIR/"
cp "$SOURCE_DIR/wgdb-postgres.volume" "$TARGET_DIR/"
render "$SOURCE_DIR/wgdb-backend.build.template" "$TARGET_DIR/wgdb-backend.build"
render "$SOURCE_DIR/wgdb-frontend.build.template" "$TARGET_DIR/wgdb-frontend.build"
render "$SOURCE_DIR/wgdb-postgres.container.template" "$TARGET_DIR/wgdb-postgres.container"
render "$SOURCE_DIR/wgdb-backend.container.template" "$TARGET_DIR/wgdb-backend.container"
render "$SOURCE_DIR/wgdb-frontend.container.template" "$TARGET_DIR/wgdb-frontend.container"

systemctl --user daemon-reload

echo "Rendered Quadlets into $TARGET_DIR"
echo "Config directory: $CONFIG_DIR"
echo "Next: create backend.env and postgres.env with mode 600, then run deployment/scripts/migrate.sh and start the services."
