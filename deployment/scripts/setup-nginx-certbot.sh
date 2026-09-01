#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "Run this script as root (sudo)." >&2
    exit 1
fi

if [[ $# -lt 3 ]]; then
    echo "Usage: sudo $0 DOMAIN EMAIL /absolute/path/to/wgdb" >&2
    exit 2
fi

DOMAIN="$1"
EMAIL="$2"
REPO_DIR="$3"
CONF_DIR="/etc/nginx/conf.d"
CONF="$CONF_DIR/wgdb.conf"
WEBROOT="/var/www/certbot"

command -v nginx >/dev/null || { echo "nginx is not installed" >&2; exit 1; }
command -v certbot >/dev/null || { echo "certbot is not installed" >&2; exit 1; }

mkdir -p "$CONF_DIR" "$WEBROOT"

render() {
    sed "s|@@WGDB_DOMAIN@@|$DOMAIN|g" "$1" > "$2"
}

render "$REPO_DIR/deployment/nginx/wgdb-http.conf.template" "$CONF"
nginx -t
systemctl reload nginx

certbot certonly \
    --webroot \
    --webroot-path "$WEBROOT" \
    --domain "$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --non-interactive

render "$REPO_DIR/deployment/nginx/wgdb-https.conf.template" "$CONF"
nginx -t
systemctl reload nginx

mkdir -p /etc/letsencrypt/renewal-hooks/deploy
cat > /etc/letsencrypt/renewal-hooks/deploy/10-reload-nginx <<'HOOK_EOF'
#!/usr/bin/env sh
set -eu
nginx -t
systemctl reload nginx
HOOK_EOF
chmod 0755 /etc/letsencrypt/renewal-hooks/deploy/10-reload-nginx

certbot renew --dry-run

echo "HTTPS configured for https://$DOMAIN"
