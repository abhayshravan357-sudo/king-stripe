# Production readiness checklist

## Implemented and locally checked

- [x] Server-side price calculation, order snapshots, bounded inputs, idempotency and scoped order access.
- [x] Razorpay adapter with checkout signature/provider status checks, signed webhook handling and event deduplication; mocked tests pass.
- [x] Admin password hashing, sessions, CSRF checks, login throttle, order/variant controls and audit records.
- [x] Configurable inventory modes, reservations and expiry; disabled by default until real policy/stock is supplied.
- [x] Restore protection, credential redaction and mocked active/non-empty target refusal tests.
- [x] 11 backend tests, 8-page static QA, secret scan, Chromium checkout/admin journey, and seven viewport widths.

## Required before public launch

- [ ] Test with the declared dependency versions in a clean environment (local FastAPI 0.110.0 is below declared minimum 0.115).
- [ ] Run PostgreSQL migrations, concurrency/API integration tests, Docker Compose and container build.
- [ ] Complete a real disposable PostgreSQL backup and restore drill.
- [ ] Run Razorpay merchant sandbox payment and provider-delivered webhook/reconciliation; keep live payment activation disabled until explicitly authorized.
- [ ] Install and run Playwright Firefox/WebKit, Lighthouse, axe/Pa11y, ZAP passive baseline, and dependency audit.
- [ ] Confirm real stock quantities and inventory policy for every variant.
- [ ] Approve currency, shipping, tax, delivery, cancellation, return/refund, privacy/retention, terms and support details.
- [ ] Configure production host/domain, HTTPS, exact CORS allowlist, managed secrets, shared/edge rate limiting, monitoring and off-site backups.
- [ ] Observe successful CI and staging runs; review production configuration and recovery objectives.

**Status:** Development implementation with local tests; **not production-ready**. No production deployment or real payment was performed.
