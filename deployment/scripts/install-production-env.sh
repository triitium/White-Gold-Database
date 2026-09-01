#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
CONFIG_DIR="${2:-$HOME/.config/wgdb}"
mkdir -p "$CONFIG_DIR"

for name in backend postgres; do
    target="$CONFIG_DIR/$name.env"
    example="$REPO_DIR/deployment/production/$name.env.example"
    if [[ ! -e "$target" ]]; then
        cp "$example" "$target"
        chmod 600 "$target"
        echo "Created $target"
    else
        echo "Keeping existing $target"
    fi
done

echo
printf '%s\n' "Edit both files and replace CHANGE_ME values before starting WGDB."
printf '%s\n' "Suggested secrets: openssl rand -hex 32"
