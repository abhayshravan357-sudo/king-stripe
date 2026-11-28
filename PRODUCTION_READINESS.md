# Production readiness

**Status: NOT READY for public launch.** Implemented code and local test evidence do not establish production operation. No public deployment or live payment configuration is active.

## Verified locally

- Server-side catalog pricing, pending checkout, idempotency, token-protected order lookup, and inventory reservation/mode logic.
- Admin auth/session/CSRF protections, order detail and fulfillment controls, per-variant availability updates, and audit events.
- Razorpay provider adapter and mocked API/signature/webhook tests. No merchant sandbox credentials or live transaction were used.
- Loopback Chromium journey for collection routes, filters/sorting, wishlist, variant selection, cart persistence/quantity/removal, checkout validation, order lookup, profile save/clear, admin authorization and inventory update; storefront/admin overflow checks from 320px through 1440px.
- Static HTML checks, Python compile, JavaScript syntax, shell syntax, secret scanning, and mocked restore-safety checks (see final report for exact latest counts).

## Launch gates still open

- PostgreSQL migrations and backup/restore drill against a real disposable PostgreSQL service; Docker/Compose startup and CI run evidence.
- Razorpay merchant sandbox credentials, real sandbox checkout/webhook/reconciliation, and externally configured callback URL.
- Approved stock policy and actual quantities for each variant; approved shipping, tax, delivery, cancellation, refund/return, privacy and support policies.
- Accessibility audit and measured Lighthouse performance results; Firefox/WebKit browser runs; OWASP ZAP run; dependency audit; production configuration review and monitoring.
- Hosting/domain, HTTPS, secret storage, off-machine backup schedule, retention and recovery objectives.

See [BLOCKERS.md](BLOCKERS.md) for remaining dependencies and decisions. Do not accept real payments or deploy publicly until critical gates are resolved and verified in an isolated staging environment.
