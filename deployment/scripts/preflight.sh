#!/usr/bin/env bash
set -euo pipefail

fail=0

need() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "MISSING: $1"
        fail=1
    else
        echo "OK: $1 -> $(command -v "$1")"
    fi
}

need podman
need systemctl
need curl

if command -v podman >/dev/null 2>&1; then
    podman --version
    podman info --format 'rootless={{.Host.Security.Rootless}} cgroup={{.Host.CgroupsVersion}} network={{.Host.NetworkBackend}}' || true
fi

if [[ -r /etc/subuid ]] && grep -q "^${USER}:" /etc/subuid; then
    echo "OK: /etc/subuid entry for $USER"
else
    echo "WARN: no /etc/subuid entry for $USER"
fi

if [[ -r /etc/subgid ]] && grep -q "^${USER}:" /etc/subgid; then
    echo "OK: /etc/subgid entry for $USER"
else
    echo "WARN: no /etc/subgid entry for $USER"
fi

if loginctl show-user "$USER" -p Linger 2>/dev/null | grep -q '=yes'; then
    echo "OK: systemd lingering enabled for $USER"
else
    echo "WARN: lingering is not enabled. An admin should run: sudo loginctl enable-linger $USER"
fi

if ss -ltn 2>/dev/null | grep -Eq '127\.0\.0\.1:(18000|18080)\b'; then
    echo "WARN: one of 127.0.0.1:18000/18080 is already in use"
fi

exit "$fail"
