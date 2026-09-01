#!/usr/bin/env bash
set -euo pipefail
systemctl --user --no-pager --full status wgdb-postgres.service wgdb-backend.service wgdb-frontend.service || true
echo
podman ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
