# API overview

Local base URL: `http://localhost:8000`. Interactive OpenAPI docs: `/docs`.

## Health and catalog

- `GET /health` is process liveness.
- `GET /ready` checks database connectivity.
- `GET /api/v1/collections` returns collections, including concept labels.
- `GET /api/v1/products` returns active products/variants and INR paise in `price_minor`.

## Checkout and payment

- `POST /api/v1/checkout-sessions` accepts `items` (`variant_id`, quantity 1–10), `name`, `email`, `address`; requires `Idempotency-Key` (16–100 chars). The server derives prices and stores snapshots. It returns a scoped order access token, order reference and status. Checkout may fail with 503 when variant inventory is not configured.
- When Razorpay test mode is configured, the API creates a provider order and returns the public key/provider reference. Live activation requires explicit configuration and remains disabled by default.
- `POST /api/v1/payments/verify` requires `X-Order-Token` and verifies the checkout signature plus fetched provider amount/currency/capture status.
- `POST /api/v1/webhooks/razorpay` validates the raw-body signature and event ID, then handles captured/failed/refund events idempotently.
- `GET /api/v1/orders/{reference}` requires the one-time token in `X-Order-Token`; missing token returns 401 and invalid token/reference returns 404. Treat the token like a password.

No shipping/tax amount is calculated. Provider integration has mocked tests only; a merchant sandbox transaction and provider-delivered webhook have not been verified.

## Admin

- `POST /api/v1/admin/login` creates a session after configured credentials pass verification. Bootstrap uses an operator-provided password hash; there is no public registration.
- `POST /api/v1/admin/logout` revokes the session and requires `X-CSRF-Token`.
- `GET /api/v1/admin/orders` and `GET /api/v1/admin/orders/{reference}` list/detail orders.
- `PATCH /api/v1/admin/orders/{reference}/fulfillment` advances valid fulfillment states and requires CSRF.
- `GET /api/v1/admin/variants`, `PATCH /api/v1/admin/variants/{variant_id}`, and `PUT /api/v1/admin/variants/{variant_id}/inventory` manage catalog price/availability and inventory configuration; mutations require CSRF.
- `GET /api/v1/admin/audit` lists operational audit events.

All admin routes require the session cookie. CORS credentials are enabled only for configured origins; set the production allowlist to the exact storefront origin. See [SECURITY.md](SECURITY.md) before exposing the API.
