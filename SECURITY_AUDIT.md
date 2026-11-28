# Security audit

**Scope:** Source review and local tests on 2026-11-27. No production target was scanned. This is not a penetration test or security certification.

## Controls observed and tested

- Checkout receives variant IDs and quantities, calculates amounts from the server catalog, validates bounded input, and records immutable item/price snapshots.
- Idempotency keys bind to a request fingerprint. Order references are random, scoped access tokens are stored as hashes, and access comparisons use constant-time helpers.
- Razorpay provider code checks test/live configuration, verifies checkout signatures and fetched payment amount/currency/captured status, validates signed webhooks, and deduplicates event IDs. Provider interactions were mocked; no real or sandbox transaction ran.
- Admin uses password hashing, expiring hashed sessions, HttpOnly/SameSite cookies, CSRF checks for mutations, login throttling, role-gated order/variant endpoints, and audit records. Browser and unit checks covered unauthorized access and authenticated order/inventory operations.
- CORS uses an explicit allowlist, including credentialed admin session requests. Compose keeps the API on loopback and does not publish the database port.
- Restore prompts hide the target URL, redact its credentials for display, reject the active database and non-empty targets, and keep credentials out of process arguments. Mocked restore safety tests passed.
- The test setup forcibly disables payment and live activation, clears provider credentials, and uses synthetic customer data and disposable SQLite files. PostgreSQL test URLs must contain `test` in the database name before destructive fixture setup is allowed.
- Local secret scan reported no high-confidence matches. This is not proof that all secrets are absent.

## Open risks and release gates

- Payment verification is not externally verified with a Razorpay merchant sandbox or provider-delivered webhook.
- Rate limiting is process-local and unsuitable across multiple workers; use edge/shared rate controls and monitor abuse before public launch.
- Production HTTPS, HSTS/CSP, host firewalling, managed secrets, monitoring, privacy/retention, backup schedule and recovery objectives remain deployment decisions.
- PostgreSQL concurrency/row locks, migrations, real backup/restore, and container startup were not verified because Docker, PostgreSQL tools and Alembic are unavailable here.
- Dependency vulnerability audit and OWASP ZAP were unavailable. No external scan was run.
- Admin stores and displays customer PII. Operational access controls, retention and deletion obligations need business approval.

## Results

- Backend tests: 11 passed (SQLite, mocked payment APIs).
- Chromium flow: passed with synthetic data, including unauthorized admin denial and authorized order/inventory operations.
- Secret scan: no high-confidence findings.
- ZAP, dependency audit, PostgreSQL and provider sandbox: not run.

