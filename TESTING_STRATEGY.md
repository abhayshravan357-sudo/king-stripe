# Testing strategy

## Checks in the repository

- Backend: `cd backend && ./.venv/bin/python -m pytest -q`. Unit tests use SQLite and mocked Razorpay calls. The optional `TEST_DATABASE_URL` path is destructive; its database name must contain `test`.
- Static QA: `cd backend && ./.venv/bin/python tests/static_qa.py` checks all HTML pages for duplicate IDs, missing local links, unlabeled form controls and missing image alt text.
- Browser journey: `cd backend && ./.venv/bin/python tests/browser_checkout.py` starts isolated loopback API/static servers with synthetic SQLite data; forces payment/live activation off; covers storefront checkout and admin behavior in Chromium, and checks 320, 375, 390, 430, 768, 1366 and 1440px widths.
- Syntax and integrity: Python `compileall`, Node `--check` for storefront/profile/admin scripts, shell `-n` for backup/restore, `python tools/secret_scan.py`, and `git diff --check`.
- CI also runs `pip-audit`, PostgreSQL migrations/seeding against a dedicated `kingstripe_test` service, Playwright Chromium, static QA, secret scanning and Docker build.

## Latest local result

On 2026-11-27, 11 backend tests passed; static QA passed for 8 HTML pages; the Chromium journey passed at all seven viewport widths for storefront and admin; Python/JavaScript/shell syntax and secret scan passed. During viewport expansion a 320px product-card metadata overflow was discovered and fixed, then the full browser journey passed again.

The test runtime inherits system packages (FastAPI 0.110.0 versus the declared `>=0.115`). A clean dependency install and CI run remain necessary. Payment calls are mocked; no provider transaction was made. No PostgreSQL server/Compose, Lighthouse, axe/Pa11y, ZAP, Firefox or WebKit run was available.

## Remaining verification

1. Run in CI with declared dependency versions and retain the actual workflow result.
2. Run migrations, concurrency/integration tests, and backup/restore against a disposable PostgreSQL service.
3. Run Playwright Firefox and WebKit on supported CI images.
4. Add and run axe-core coverage for all pages/dialogs, followed by keyboard and screen-reader review. Obtain repeated Lighthouse measurements on a stable build.
5. Run dependency audit and ZAP passive baseline against isolated staging. Active scans must target only an explicitly controlled environment.
6. Use Razorpay sandbox credentials/webhook to verify complete redirects, captured payment and reconciliation, with synthetic customer data.
7. Keep reports, screenshots/traces and artifacts; do not report unavailable tools as passing.

