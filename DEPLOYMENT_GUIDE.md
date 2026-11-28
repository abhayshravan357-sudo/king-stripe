# Deployment and recovery guide

## Laptop

Install Docker Compose. In `backend/`, copy `.env.example` to `.env`, set a random 64-character hexadecimal `POSTGRES_PASSWORD`, then run `docker compose up --build`. Stop with `docker compose down`; the named PostgreSQL volume remains. Serve the static site from the repository root with `python3 -m http.server 8080`. API: `http://127.0.0.1:8000`; readiness: `/ready`.

The API binds to loopback and PostgreSQL has no published host port. Keep it that way on a personal laptop. Compose runs migrations and seeds the current catalog when the API starts.

## Admin provisioning

In `backend/`, run `python -m app.hash_password` with installed backend dependencies, then put the resulting hash and a chosen `ADMIN_USERNAME` in `.env`. Restart the API. Access `http://localhost:8080/admin.html`. Do not put credentials in frontend files; no registration endpoint exists.

## Payments and availability

Payment provider defaults to disabled and live payments default to false. To prepare a sandbox, configure the Razorpay test key ID, API secret, webhook signing secret, and `PAYMENT_PROVIDER=razorpay`; configure the webhook URL only after an approved staging host exists. No Razorpay transaction has been performed. Inventory defaults to disabled; choose an operating mode and set actual variant quantities using admin. Do not accept real orders until the business policies listed in `BLOCKERS.md` are approved.

## Backup and restore

Install PostgreSQL client tools. Set `DATABASE_URL` in the process environment, then run `./backup.sh` from `backend/`; it writes a private custom-format dump under `backend/backups/`. Store encrypted copies off-machine on an operator-chosen schedule.

To restore, run `./restore.sh BACKUP.dump`. Enter a separate target database URL at the hidden prompt, then type `RESTORE`. The helper refuses the configured active database and refuses a non-empty target. Verify the restored database and application before changing active configuration. The restore helper is covered with mocked commands; no real PostgreSQL restore drill has been run here.

## Later VPS deployment

Select the host, domain, budget, and operator access first. Use host-managed secrets, TLS termination, restricted database access, exact HTTPS CORS origins, monitoring, encrypted off-site backups, and periodic restore drills. Cloudflare Tunnel is documented as a future option only; none is installed or activated. Do not publish the laptop directly.
