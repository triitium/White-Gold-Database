# WGDB deployment: rootless Podman + Quadlet + host nginx

## Production topology

```text
Internet
   |
   | TCP 80/443 only
   v
host nginx + Certbot
   |-- /api/* -> 127.0.0.1:18000 -> rootless WGDB backend
   `-- /*     -> 127.0.0.1:18080 -> rootless WGDB frontend

rootless Podman network "wgdb"
   backend -> postgres:5432
   postgres -> named volume wgdb-postgres-data
```

nginx is deliberately a host service rather than a rootless container. Rootless Podman cannot normally bind host ports below 1024, so this preserves rootless isolation for application containers without changing the host-wide privileged-port sysctl.

## Pinned production components (22 Aug 2026)

- PostgreSQL: `18.6-alpine`
- nginx frontend image: `1.30.4-alpine`
- Python base: `3.14-slim`
- Node build base: `24-alpine`
- React: 19.2.8
- React Router: 8.3.0
- Vite: 8.2.1

## Oracle VM prerequisites

Install Podman with Quadlet support, nginx, Certbot, Git and curl. Create a dedicated Linux user, recommended name `wgdb`, then enable its user systemd manager at boot:

```bash
sudo loginctl enable-linger wgdb
```

Rootless Podman needs valid `/etc/subuid` and `/etc/subgid` ranges for this user. Do not blindly copy UID ranges from another host; ensure they do not overlap existing allocations.

In Oracle Cloud networking and the host firewall, expose only TCP 22 (SSH as required), 80 and 443. Do not expose 5432, 8000, 18000, 8080 or 18080.

## Recommended checkout

As user `wgdb`:

```bash
cd ~
git clone <your-repository> wgdb
cd ~/wgdb
```

## 1. Preflight

```bash
./deployment/scripts/preflight.sh
```

## 2. Production environment files

```bash
./deployment/scripts/install-production-env.sh
nano ~/.config/wgdb/postgres.env
nano ~/.config/wgdb/backend.env
```

Generate URL-safe secrets with `openssl rand -hex 32`. Use one as the PostgreSQL password in both env files and another as `SECRET_KEY`.

## 3. Install/render Quadlets

```bash
./deployment/scripts/render-quadlets.sh
./deployment/scripts/build.sh
```

Quadlets are rendered into `~/.config/containers/systemd/`. Podman generates normal user services from them. The app network and volume are declarative Quadlet units too.

## 4. Start PostgreSQL and migrate

```bash
./deployment/scripts/migrate.sh
```

Migrations are intentionally explicit; they are not blindly run on every backend restart.

## 5. Create first admin

```bash
./deployment/scripts/create-admin.sh
```

## 6. Start application

```bash
./deployment/scripts/start.sh
curl http://127.0.0.1:18000/health
curl http://127.0.0.1:18080/healthz
```

Useful commands:

```bash
systemctl --user status wgdb-postgres wgdb-backend wgdb-frontend
journalctl --user -u wgdb-backend -f
podman ps
podman healthcheck run wgdb-postgres
```

## 7. Host nginx + TLS

Point DNS at the Oracle VM and make sure port 80 is reachable. Install nginx and Certbot using the package method appropriate for the VM OS, then run:

```bash
sudo ./deployment/scripts/setup-nginx-certbot.sh wgdb.example.com you@example.com /home/wgdb/wgdb
```

The script installs an HTTP-only ACME config, obtains the certificate via Certbot webroot mode, swaps in the HTTPS config, adds an nginx reload renewal hook and runs a Certbot dry-run renewal test.

## 8. Daily backups

```bash
./deployment/scripts/install-backup-timer.sh
```

Backups default to `~/backups/wgdb/wgdb-YYYYMMDD-HHMMSS.dump`, get SHA-256 sidecars and have 30-day local retention. A local backup on the same VM is not disaster recovery; copy/encrypt at least one backup off the VM.

Restore is deliberately interactive:

```bash
./deployment/scripts/restore.sh ~/backups/wgdb/wgdb-....dump
```

## Updating WGDB

After pulling reviewed code:

```bash
git pull --ff-only
./deployment/scripts/render-quadlets.sh
./deployment/scripts/update.sh
```

The update sequence is build -> Alembic migration -> backend restart -> frontend restart -> loopback health checks.

## Local Podman Compose

```bash
cp deployment/local/.env.example deployment/local/.env
podman compose --env-file deployment/local/.env up --build -d
podman compose --env-file deployment/local/.env exec backend alembic upgrade head
```

Open `http://localhost:8080`. Backend is available on loopback at `http://localhost:8000`.

`podman compose` is only the convenient local workflow. Production uses Quadlet/systemd.
