#!/usr/bin/env bash
set -euo pipefail
systemctl --user stop wgdb-frontend.service wgdb-backend.service wgdb-postgres.service
