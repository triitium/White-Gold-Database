#!/usr/bin/env bash
set -euo pipefail

systemctl --user daemon-reload
systemctl --user restart wgdb-backend-build.service
systemctl --user restart wgdb-frontend-build.service

echo "Images:"
podman images --format '{{.Repository}}:{{.Tag}}  {{.Id}}' | grep 'localhost/wgdb-' || true
