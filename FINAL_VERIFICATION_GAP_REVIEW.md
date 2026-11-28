# Final verification gap review

**Reviewed:** 2026-11-27  
**Recommendation:** The proposed verification prompt is directionally sound. Keep public deployment and live payment out of scope. Reorder the work slightly and add the provider-order retry case below.

## Executive assessment

The current code and recorded local evidence support the claim that core development flows have been tested. They do not establish production readiness. The declared dependency minimum is not represented by the local Python environment; PostgreSQL, migrations, Docker and recovery have not been executed; the provider has only mocked tests; and the browser/accessibility/security/performance matrix is incomplete.

One code-level reliability case should be tested and fixed before sandbox sign-off: if Razorpay accepts an order but the response is lost, the local order can remain without `provider_order_id`. Retrying the same checkout key tries to create the provider order again using the same `receipt`. Razorpay documents that a repeated receipt is rejected as a duplicate. The retry path needs a provider reconciliation strategy so a legitimate customer is not left with an unpayable pending order. See the [Razorpay Orders API](https://hdfcbank-collectnow-docs.razorpay.com/api/orders/create/) and the retry flow in `backend/app/main.py` / `backend/app/services/payments.py`.

## Gate status

| Gate | Status | What is evidenced / what remains |
|---|---|---|
| Existing local backend suite | **VERIFIED (latest recorded)** | 11 tests passed on SQLite with mocked provider calls. The runtime is not clean and uses FastAPI 0.110.0 despite the declared `>=0.115,<1`. |
| Static frontend checks | **VERIFIED (latest recorded)** | 8 HTML pages passed the repository static checker; JavaScript and shell syntax, compile checks and secret scan passed. |
| Chromium journeys and responsive checks | **VERIFIED (latest recorded)** | Checkout/admin/profile journeys and seven viewport widths passed. This proves Chromium only. |
| Clean dependency installation | **BLOCKED** | `backend/.venv/pyvenv.cfg` enables `include-system-site-packages`; FastAPI 0.110.0 is being inherited. Create a fresh Python 3.12 environment with system packages disabled and install the declared requirements. Local PyPI access previously failed; use a working package index/CI runner rather than weakening constraints. |
| PostgreSQL migrations and behavior | **BLOCKED** | `0001` and `0002` are explicit Alembic operations with non-overlapping schema responsibilities on inspection. No Alembic/PostgreSQL run is recorded. Exercise empty-database upgrade, constraints, transactions, rollback, duplicate checkout, payment transitions and row-lock inventory behavior against a disposable database. |
| Downgrade behavior | **VERIFIED AS INTENTIONALLY UNSUPPORTED** | Both migrations refuse destructive downgrade. Keep forward-only migrations and document restore/forward-migration recovery as the supported procedure; do not treat downgrade as a passing gate. |
| Docker and CI execution | **BLOCKED** | A PostgreSQL-backed GitHub Actions workflow is configured for migrations, tests, static QA, Chromium, secret scan, `pip-audit` and image build. No successful workflow result or local Docker run is recorded. Run it after dependency and migration verification. |
| Razorpay integration | **BLOCKED** | Order amount units, receipt use, checkout signature and raw-body webhook verification follow the documented integration patterns. Mocked tests are not a merchant sandbox transaction. Add retry reconciliation for duplicate receipts, then verify success, failure, abandoned checkout, delayed/out-of-order events, refunds, and provider-delivered webhooks in test mode. |
| Dependency/security scans | **BLOCKED** | Secret scan passed; `pip-audit` is in CI but has no observed result. ZAP was not run. Run dependency audit and a passive ZAP baseline against isolated staging; add active tests only to an explicitly controlled local/staging target. |
| Accessibility/performance | **NOT STARTED** | No axe/Pa11y or Lighthouse result. Add axe coverage for each route and interactive dialog, manual keyboard/screen-reader checks, and repeated mobile/desktop Lighthouse runs. Do not claim WCAG conformance or target scores until measured. |
| Firefox/WebKit | **NOT STARTED** | Workflow currently installs Chromium only and the smoke script launches Chromium. Parameterize the same journeys by Playwright browser and add Firefox/WebKit installs/runs in CI. |
| PostgreSQL backup/recovery | **BLOCKED** | Restore guards have mocked tests, but no actual `pg_dump` / `pg_restore` drill has been completed. Use a disposable PostgreSQL test database and verify representative restored records plus application readiness. |
| Production configuration / business inputs | **REQUIRES HUMAN APPROVAL** | Inventory mode/quantities, shipping, tax, delivery, return/refund, privacy/retention and support details need business approval. Domain/host, TLS, secret storage, monitoring, backup retention and recovery objectives need operator decisions. Live payment activation and publication remain unauthorized. |

## Changes needed in the proposed prompt

1. **Add a payment-create timeout/retry scenario.** Simulate Razorpay accepting `POST /orders` while the response is lost; retry the same local idempotency key and prove recovery of the original provider order rather than an unrecoverable duplicate-receipt error.
2. **Keep the current migration shape and run it.** The migrations are already explicit. Verify them against PostgreSQL instead of rewriting them based on a stale assumption. Their downgrade refusal is intentional; record that rollback is by reviewed forward migration or verified restore.
3. **Make browser tests parameterized.** The existing journey hardcodes Chromium. Add Firefox and WebKit runs in CI after installing their Playwright browser engines.
4. **Run in a genuinely clean environment.** Recreate the venv without system-site packages, capture `python --version`, `pip freeze`, and `pip check`, and run the full suite. The local environment cannot satisfy this until package-index access is available.
5. **Add refund and webhook ordering cases.** Mock full and partial `refund.processed`, duplicate refund event, failed-then-captured, captured-then-failed, and invalid/rotated webhook secret cases. Current event handling has some ordering/idempotency protection, but external delivery remains unverified.
6. **Separate configured checks from observed results.** CI contains `pip-audit`, but no workflow run was observed. ZAP/axe/Lighthouse are not currently in the workflow. Report each as BLOCKED or NOT STARTED until its result exists.
7. **Refresh stale documentation.** `IMPROVEMENT_BACKLOG.md` still lists implementing Razorpay verification and admin order management as unfinished. `DECISIONS.md` still says no admin route exists. Update these to reflect that the code is implemented and the outstanding work is external sandbox/production verification.
8. **Use gate statuses in the final report.** Add one status per gate (VERIFIED, FAILED, BLOCKED, NOT STARTED, or REQUIRES HUMAN APPROVAL), plus command, environment/tool version and evidence location.

## Razorpay documentation comparison

- The implementation sends integer currency subunits and uses the local order reference as `receipt`, which is within the Orders API's documented receipt length; Razorpay also treats duplicate receipt values as duplicates.
- Checkout verification uses the server-stored provider order ID with the payment ID in the HMAC input, matching the signature procedure.
- Webhook verification uses the raw request bytes and HMAC-SHA256, and records the provider event ID for deduplication. Razorpay documents at-least-once delivery and that event order is not guaranteed, so those cases need explicit tests.

References: [Create an Order](https://hdfcbank-collectnow-docs.razorpay.com/api/orders/create/), [Standard Checkout signature verification](https://hdfcbank-collectnow-docs.razorpay.com/payments/payment-gateway/flutter-integration/standard/integration-steps/), [Validate and Test Webhooks](https://hdfcbank-collectnow-docs.razorpay.com/webhooks/validate-test/), [Webhook best practices](https://hdfcbank-collectnow-docs.razorpay.com/webhooks/best-practices/).

## Suggested execution order

1. Fix stale backlog/decision documentation and add the provider-order retry test/fix.
2. Get an isolated dependency installation with supported versions; run backend tests.
3. Run PostgreSQL migrations, integration/concurrency tests, and a real disposable backup/restore drill.
4. Run the GitHub Actions workflow; fix failures and retain artifacts.
5. Complete mocked edge cases, then the merchant Razorpay sandbox flow when credentials and webhook setup are available.
6. Run Firefox/WebKit, axe, Lighthouse, dependency audit and ZAP against controlled targets.
7. Review business and operational inputs. Keep the result **NOT READY FOR PUBLIC LAUNCH** until these gates are closed.

