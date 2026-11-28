# Blockers and launch requirements

Updated: 2026-11-27

## External setup / business input

- Eligible Razorpay merchant account, test credentials and webhook secret are needed to run the actual provider sandbox. Live payments remain disabled and require explicit authorization.
- Define variant stock and select an inventory mode. No inventory quantity is preloaded.
- Supply approved shipping, tax, delivery, cancellation, refund/return, privacy, and customer-support policies before accepting real orders.
- Decide production domain/host, budget, secret storage, operator access, retention, monitoring, and recovery objectives.

## Environment / verification gaps

- PyPI DNS/network access failed during dependency installation; no requirements were removed or weakened.
- Docker and PostgreSQL client/server tools are unavailable locally. The CI workflow defines PostgreSQL-backed migration and tests, but no CI run has been observed.
- No locally available Lighthouse, axe/Pa11y, or OWASP ZAP run; no measured Lighthouse scores or WCAG conformance claim is available.
- Playwright Chromium is verified. Firefox and WebKit Playwright runs are unavailable; a system Firefox binary alone does not establish Playwright compatibility.
- No real Razorpay sandbox transaction, webhook, PostgreSQL restore drill, production config review, public HTTPS deployment, or production monitoring has been verified.

These gaps mean this repository is not ready for public launch.
