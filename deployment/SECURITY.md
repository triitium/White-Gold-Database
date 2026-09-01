# WGDB production security notes

- Application containers run rootless under the dedicated `wgdb` Linux user.
- nginx/Certbot stay on the host because TCP 80/443 are privileged ports.
- Rootless application ports bind to loopback only: `127.0.0.1:18000` and `127.0.0.1:18080`.
- PostgreSQL publishes no host port.
- Production cookies use `Secure` + `HttpOnly` for the JWT and the established CSRF double-submit token.
- PostgreSQL host authentication initializes with SCRAM-SHA-256.
- Secret environment files belong in `~/.config/wgdb` with mode `0600` and are gitignored.
- TLS is handled by nginx with Certbot renewal.
- HSTS is enabled only in the final HTTPS configuration.
- AuditLog remains append-only at the application layer.
- Hard delete remains admin-only and requires prior soft delete.
- Backups are custom-format `pg_dump` files with SHA-256 checksums; off-VM backup is still required.

## Public ports

```text
22/tcp  SSH, if desired
80/tcp  ACME + HTTPS redirect
443/tcp WGDB
```

Do not publicly expose PostgreSQL or the application loopback ports.

## Rootless port note

Do not lower `net.ipv4.ip_unprivileged_port_start` just to let a rootless nginx container own 80/443 unless that host-wide policy change is intentional. Host nginx avoids needing it.
