# King Stripe QA audit

**Audit date:** 2026-11-27  
**Scope:** Current repository state, including payment provider, admin, inventory, recovery and browser-test additions. Local synthetic data only; no production site or live payment was used.

## Assessment

King Stripe has materially advanced since the previous audit. Core checkout, payment-provider adapter, admin operations, inventory configuration, idempotency and recovery protections now have implementation and local test coverage. The app is **still not ready for public launch** because real PostgreSQL/Compose, provider sandbox, accessibility/performance/security scanning and production operation have not been verified; business policies and stock data are not supplied.

## Verified

- Backend suite: **11 passed** using SQLite and mocked provider interactions.
- Static QA: **8 HTML pages passed** for duplicate IDs, local links, labels, and image alt text.
- Chromium smoke journey passed: catalog → variant selection → persistent bag → pending order → scoped order lookup; unauthenticated admin is denied; authenticated admin can inspect the order and update inventory; fulfillment cannot advance before payment.
- Storefront and admin were checked at 320, 375, 390, 430, 768, 1366 and 1440px widths with no horizontal overflow.
- The 320px check exposed product metadata overflow. The mobile card layout now stacks metadata vertically; the full Chromium journey and viewport sweep passed after the fix.
- Python compile, JavaScript syntax, shell syntax, and `git diff --check` passed.
- Secret scan: no high-confidence matches in working tree or scanned Git text history.
- Restore safety tests exercise credential redaction and refusals for active/non-empty targets.
- Test setup forcibly disables payments/live mode and uses synthetic customer values. PostgreSQL test fixture now refuses an unlabelled database name.

## Not verified / blocked

- Local Python 3.12.3 environment has FastAPI 0.110.0 while requirements declare `>=0.115`; pytest passed on the inherited environment, so a clean install against declared versions remains required. PyPI was unreachable during dependency installation.
- No Docker, PostgreSQL server/client, Alembic, or psycopg: PostgreSQL migrations, concurrency, backup/restore drill and container build are unverified.
- Playwright Chromium is installed and passed. Firefox and WebKit Playwright engines are not installed/run.
- Lighthouse, axe/Pa11y, OWASP ZAP and `pip-audit` were unavailable. No score, WCAG conformance, or vulnerability-free claim is made.
- No CI run, public staging, external payment sandbox, production TLS/hosting, monitoring or live operation was observed.

## Material release blockers

- Obtain and run an approved Razorpay sandbox account/webhook setup; live payments remain disabled.
- Choose the stock policy and enter accurate stock for each variant. Inventory mode defaults to disabled.
- Approve shipping, taxes, delivery/cancellation, refund/return, privacy and support information.
- Configure hosting/domain, HTTPS, production secrets, edge/shared rate limits, monitoring, retention and off-site backups; complete a PostgreSQL restore drill.
- Complete accessibility, Lighthouse, dependency and ZAP scans in isolated staging.

See [KING_STRIPE_FINAL_PRODUCTION_REPORT.md](KING_STRIPE_FINAL_PRODUCTION_REPORT.md) for details and commands.
