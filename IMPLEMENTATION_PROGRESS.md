# Implementation progress

Updated: 2026-11-27

## Implemented

- Server-priced order creation with immutable item snapshots, idempotency keys, private order access tokens, and transaction-safe inventory reservations.
- Razorpay Orders API adapter, hosted checkout handoff, payment signature and captured-status verification, signed webhook validation, event de-duplication, and guarded payment/order transitions. Live payments default off.
- Private admin login with PBKDF2 password verification, expiring HttpOnly sessions, CSRF checks, login rate limits, order search/detail, fulfillment updates, inventory policy/stock edits, and audit events.
- PostgreSQL migrations, local Compose configuration, health/readiness checks, backup and guarded restore tools, CI workflow, and deployment/setup documentation.
- Storefront-to-admin Chromium journey and static markup checks.

## Checks actually run

- Backend tests: 11 passed, with third-party Starlette and pytest-asyncio deprecation warnings.
- Chromium storefront/admin journey: passed on rerun, using disposable SQLite, synthetic buyer/admin data, and pending-payment mode. One earlier run failed on a timing-sensitive admin-row assertion; the test now waits for the row. Screenshots are written to `/tmp/kingstripe-desktop.png`, `/tmp/kingstripe-mobile.png`, and `/tmp/kingstripe-admin.png`.
- Static HTML checks: 8 pages passed.
- Python compilation, JavaScript syntax, and shell syntax checks passed.
- Secret scan: no high-confidence patterns in the working tree or scanned Git text history after replacing long synthetic fixture passwords.
- `git diff --check` passed.

## Still unverified or blocked

- Fresh dependency installation failed because the package index could not resolve in this environment. The project `.venv` uses existing Python 3.12 site packages (including FastAPI 0.110, below the declared `>=0.115` minimum); Alembic and psycopg are absent. Declared requirements were not weakened, so passing local tests are not a clean install verification.
- PostgreSQL migrations, Docker image/Compose, backup and restore against a real PostgreSQL server, dependency audit, Lighthouse, axe/Pa11y, OWASP ZAP, and Firefox/WebKit remain unverified because required packages/services/tools or sandboxed access are unavailable.
- Razorpay credentials and merchant account are absent, so provider calls, hosted sandbox checkout, webhook delivery, and payment reconciliation were not exercised against Razorpay.
- Inventory is configurable, but actual stock and the operating mode for each variant remain a store decision. Shipping, tax, refund/return, delivery, privacy, and support policies also need business input.

Current status: functional development prototype; not production-ready and not publicly deployed.
