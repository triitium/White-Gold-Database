#!/usr/bin/env bash
set -euo pipefail

systemctl --user daemon-reload
systemctl --user start wgdb-postgres.service
systemctl --user start wgdb-backend.service
systemctl --user start wgdb-frontend.service

systemctl --user --no-pager --full status wgdb-postgres.service wgdb-backend.service wgdb-frontend.service || true
