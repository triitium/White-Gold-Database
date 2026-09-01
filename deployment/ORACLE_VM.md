# Oracle VM deployment checklist

This is deliberately OS-neutral because an Oracle Cloud VM may run Oracle Linux, Ubuntu, Debian, etc.

## Host

- [ ] DNS A/AAAA points at the VM.
- [ ] Oracle Cloud security list / NSG allows TCP 80 and 443.
- [ ] Host firewall allows TCP 80 and 443.
- [ ] PostgreSQL and WGDB loopback ports are **not** opened publicly.
- [ ] nginx is installed and enabled.
- [ ] Certbot is installed.
- [ ] Podman has Quadlet support.
- [ ] Dedicated `wgdb` user exists.
- [ ] `wgdb` has valid, non-overlapping `/etc/subuid` and `/etc/subgid` ranges.
- [ ] `sudo loginctl enable-linger wgdb` has been run.

## WGDB user

- [ ] Repository checked out.
- [ ] `deployment/scripts/preflight.sh` passes or warnings are understood.
- [ ] `~/.config/wgdb/backend.env` is mode 0600.
- [ ] `~/.config/wgdb/postgres.env` is mode 0600.
- [ ] DB password matches in both files.
- [ ] `SECRET_KEY` is random and not committed.
- [ ] TMDB token is configured if TMDB import is wanted.
- [ ] Quadlets rendered.
- [ ] Images built.
- [ ] Alembic migration completed.
- [ ] First admin account created.
- [ ] backend/frontend/PostgreSQL health checks pass on loopback.

## TLS

- [ ] HTTP challenge is reachable from the internet.
- [ ] Certbot certificate obtained.
- [ ] `nginx -t` succeeds.
- [ ] `certbot renew --dry-run` succeeds.
- [ ] HTTPS login works and browser shows `Secure` cookies.

## Data

- [ ] Excel import dry-run reviewed before `--commit`.
- [ ] Daily backup timer enabled.
- [ ] At least one restore test has been performed on a non-production DB.
- [ ] At least one encrypted/off-VM copy of backups exists.
