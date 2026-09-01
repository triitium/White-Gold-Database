#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
TARGET_DIR="$HOME/.config/systemd/user"
mkdir -p "$TARGET_DIR"

sed "s|@@WGDB_REPO@@|$REPO_DIR|g" \
    "$REPO_DIR/deployment/systemd/wgdb-backup.service" \
    > "$TARGET_DIR/wgdb-backup.service"
cp "$REPO_DIR/deployment/systemd/wgdb-backup.timer" "$TARGET_DIR/wgdb-backup.timer"

systemctl --user daemon-reload
systemctl --user enable --now wgdb-backup.timer
systemctl --user list-timers wgdb-backup.timer --no-pager
