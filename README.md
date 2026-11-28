# King Stripe

King Stripe is a static storefront with a FastAPI/PostgreSQL backend. Checkout prices are derived from the server catalog; payment, admin, inventory, backup, and deployment controls are implemented with payments and inventory disabled until configured. This is a development prototype, not a public store launch.

## Local laptop run

1. Install Docker Compose. In `backend/`, copy `.env.example` to `.env` and set `POSTGRES_PASSWORD` to a random 64-character hexadecimal string. Keep `.env` private.
2. From `backend/`, run `docker compose up --build`.
3. From the repository root, in a second terminal run `python3 -m http.server 8080`.
4. Open `http://localhost:8080`. API docs are at `http://localhost:8000/docs`; liveness and database readiness are `/health` and `/ready`.

Compose binds the API to `127.0.0.1`; PostgreSQL has no published host port. Do not expose the laptop publicly.

## Admin setup

Generate a password hash using `cd backend && python -m app.hash_password`, set `ADMIN_USERNAME` and `ADMIN_PASSWORD_HASH` in `backend/.env`, then restart Compose. Admin page: `http://localhost:8080/admin.html`. There is no public admin registration.

## Tests

From `backend/`, run `python -m pytest -q`, `python tests/static_qa.py`, and `python tests/browser_checkout.py` (requires Playwright and Chromium). The browser journey binds only to loopback and uses disposable SQLite and synthetic data. The CI workflow adds PostgreSQL migrations, dependency audit, browser install, and Docker build.

## Current controls and decisions

- `PAYMENT_PROVIDER=disabled`, `ALLOW_LIVE_PAYMENTS=false`, and `INVENTORY_MODE=disabled` are defaults. Pending orders are not paid orders.
- Razorpay test mode is implemented but requires merchant test credentials and an approved webhook configuration to verify end-to-end.
- Set actual variant availability and stock policy in the admin; quantities are not invented.
- Shipping, tax, delivery, cancellation, refund/return, privacy, and support policies must be supplied by the business.
- Backup/restore and laptop deployment instructions are in [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) and [BACKUP_AND_RECOVERY.md](BACKUP_AND_RECOVERY.md).
- Read [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md), [BLOCKERS.md](BLOCKERS.md), and [DECISION_LOG.md](DECISION_LOG.md) before planning any launch.
