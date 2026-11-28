# Backend Implementation Plan

> This document captures the initial repository assessment and scope. The implementation status below reflects later additions; see `README.md` and `KING_STRIPE_FINAL_PRODUCTION_REPORT.md` for current details.

## 1. Repository inspection

- The site is a static storefront built with HTML, CSS, and vanilla JavaScript. Pages are `index.html`, `collections/index.html`, and four collection pages. Shared behavior and the current product catalog live in `assets/js/king-stripe-collections.js`.
- There is no frontend framework, package manifest, server, API, database, authentication, or deployment configuration in the repository. Git has an `origin` remote; no application code currently depends on a backend.
- The current catalog has six hoodie products, INR prices, garment colors and sizes, and four collections. The tiger collection is the only one with products; the others are marked as concepts. Product/cart/wishlist data are hardcoded or kept in `localStorage`.
- Checkout is explicitly a preview: the form says it does not send details or process payment. Its submit handler clears the bag and displays a demo confirmation. Thus no personal or payment data currently reaches a server.
- Artwork and other media are static repository assets (SVG/PNG). There is no upload or admin interface, and no need to store media in a database or add object storage for the current experience.
- No existing server API, database, authentication, or backend dependency was found. The repository has no visible test, CI, Docker, or deployment setup.

## 2. Required backend scope

To turn the current demo into a functional store, the minimum backend should:

1. Serve the product and collection catalog from a versioned read-only API, with the server as the price/availability authority.
2. Validate a submitted cart and customer shipping/contact details, calculate totals server-side, and create a pending order.
3. Create a hosted payment session with the selected payment provider without exposing secrets in the browser.
4. Accept and verify payment-provider webhooks, then update order/payment state idempotently. A browser redirect alone must never mark an order paid.
5. Expose order confirmation/status only through an unguessable, scoped token or another deliberately selected customer access method.

Public customer accounts, password reset, media upload, inventory management, discount engine, and server-side wishlists remain out of scope. The later autonomous implementation direction requests secure admin management; that milestone is still pending because an operator/bootstrap authentication method and audit/retention policy have not been configured. The wishlist can stay browser-local unless cross-device persistence is required.

## 3. Proposed architecture

- One modular FastAPI application using Python, Pydantic, SQLAlchemy, Alembic, and PostgreSQL, as requested.
- Modules: `core` (settings, logging, errors), `api/v1` (catalog, checkout, webhook, order status), `db` (engine/session/base), `models`, `schemas`, and `services` (catalog, orders, payments). Keep repository abstractions only where they add value.
- Static frontend remains in place and calls `/api/v1`; production hosting can serve the static files and API under one site origin through the chosen platform/reverse proxy. Local dev can use separate ports with explicit CORS origins.
- Payment provider: Stripe is a plausible hosted-checkout choice based on the repository name, but the project does not currently declare it. Confirm provider, account/country availability, and INR settlement before implementing that integration.
- Media remains static in the repo initially. If product uploads become a requirement, add S3-compatible object storage and metadata then.

## 4. Proposed database schema

Keep the schema small and normalized:

- `collections`: id, slug (unique), title, description, status, artwork path, created/updated timestamps.
- `products`: id, collection_id (FK), slug (unique), name, description, garment type, active flag, created/updated timestamps.
- `product_variants`: id, product_id (FK), SKU (unique), color, size, price in minor currency units, currency, active flag; unique product/color/size constraint and indexes for product and SKU. Inventory quantity is omitted until stock tracking is defined.
- `orders`: id, public order reference (unique), status, customer name/email, shipping address fields, currency, subtotal/total in minor units, payment provider/session reference (unique where present), confirmation token hash, timestamps.
- `order_items`: id, order_id (FK), product/variant references, immutable name/SKU/color/size/price snapshots, quantity, line total. Preserve snapshots so catalog changes do not rewrite past orders.
- Optional `payment_events`: provider event id (unique), event type, received/processed timestamps and minimal processing status, to support webhook idempotency. Avoid storing card data or unnecessary webhook payload/customer personal data.

Use PostgreSQL constraints and transactions; never trust browser-submitted prices or totals. Store INR as integer paise if INR is confirmed. Keep secrets and provider credentials outside the database.

## 5. API endpoint plan

All routes are under `/api/v1`:

- `GET /health` — liveness; `GET /ready` — readiness including database connectivity.
- `GET /collections` and `GET /collections/{slug}` — active collection data.
- `GET /products` and `GET /products/{slug}` — active products and variants; optional bounded pagination/filtering if catalog growth requires it.
- `POST /checkout-sessions` — validate variant IDs/SKUs and quantities, fetch server-side prices, create pending order and hosted payment session; rate-limit and validate origin/input.
- `POST /webhooks/{provider}` — verify provider signature against raw request body and process events idempotently.
- `GET /orders/{public_reference}` — return limited order status using a scoped confirmation token; exact token transport and expiry need a decision.

Use typed request/response schemas, consistent error shapes, appropriate status codes, and generated OpenAPI docs. Do not expose administrative endpoints until an admin workflow and access policy are defined.

## 6. Frontend integration requirements

- Move the canonical catalog from the JavaScript array to the API, while preserving the existing page layout and artwork.
- Continue using the local cart as a convenience, but submit only variant identifiers and quantities; backend resolves the current price and availability.
- Replace the demo checkout form's behavior with API session creation and a redirect to hosted checkout. Clear the client cart only after a confirmed successful return/status, and treat the webhook as payment source of truth.
- Show API errors and loading states accessibly. Restrict production API origins/CORS to the deployed site.
- Decide whether collection concepts should be API-visible or remain static editorial content until products exist.

## 7. Security and reliability requirements

- Typed validation, parameterized ORM queries, bounded request sizes, rate limiting on checkout/order lookups, strict production CORS, HTTPS, security headers, and generic client-facing errors.
- Keep secrets in deployment environment/secret manager; `.env.example` contains placeholders only. Never log addresses, email, payment secrets, or full webhook bodies.
- Verify webhook signatures, enforce unique event IDs, and make event/order transitions idempotent. Never accept client-supplied prices or a client assertion of payment success.
- Use least-privilege database credentials, connection pooling, transaction boundaries, timeouts, and migrations reviewed before deployment.
- No passwords are needed without accounts. No CSRF defense is required for a stateless hosted-checkout initiation endpoint if it uses appropriate origin validation and does not rely on ambient cookie authentication; revisit if sessions/admin login are added.

## 8. Deployment, tests, and operations

- Provide a Python Docker image and local Compose PostgreSQL setup. Keep production PostgreSQL private and use managed hosting for app/database where affordable.
- Apply Alembic migrations as a deliberate release step, not an unreviewed destructive startup action. Add health/readiness probes and structured logs.
- Add GitHub Actions for formatting/linting, pytest, dependency audit, and container build validation. Use isolated test database configuration and mocked payment-provider calls for unit/API tests; add a staging webhook integration before launch.
- Document backups, restore drills, migration rollback limits, secret rotation, staging/production separation, and deployment rollback. Hosting provider is not selected yet, so provider-specific deployment wiring is pending.

## 9. Implementation phases

1. **Plan and decisions:** confirm payment provider, currency/markets, shipping/tax/returns, hosting, admin and inventory needs.
2. **Foundation:** FastAPI settings, logging, error handling, API versioning, health/readiness, Docker and local Compose.
3. **Catalog/database:** models, PostgreSQL configuration, initial Alembic migration, catalog read APIs and seed/import process for the six current products.
4. **Orders and checkout:** order schema/service, server-side totals, hosted payment session, webhook verification/idempotency, scoped order status.
5. **Frontend integration:** replace catalog source and demo checkout behavior while retaining current visual frontend; keep wishlist local unless requirements change.
6. **Security and verification:** test validation, order/payment state transitions, webhook replay, rate limits and frontend checkout flow; dependency/security checks.
7. **Deployment readiness:** production container settings, CI, staging deployment instructions, backup/recovery and readiness audit.

## 10. Risks and open decisions

- A payment provider, merchant account, currency, supported countries, tax treatment, shipping charges, refund/return policy, and fulfillment process are not specified. These affect checkout and order data and must be settled before real payments.
- No stock quantities or SKU definitions exist; selling without inventory policy can result in overselling. Initial launch may use unlimited/preorder behavior only if explicitly chosen.
- Hosting provider, domain/origin, budget, and database backup retention are unknown.
- The initial review found no admin interface. A session-protected admin console and authenticated order/variant endpoints were added later; their production deployment and operational review remain open.
- Customer addresses and order records are personal data. Define retention, access, and privacy notice before launch.
- Existing product/collection content is illustrative and should be checked for final commercial accuracy before loading into production.

## Current readiness

The current implementation includes a FastAPI/PostgreSQL backend, Razorpay adapter, pending and paid order state handling, admin operations, inventory controls, rate limiting, recovery helpers, local Compose setup and frontend integration. External payment validation, PostgreSQL recovery, production deployment, infrastructure-grade rate limiting and business policies remain incomplete; see `PRODUCTION_CHECKLIST.md`. The project remains a development prototype, not a production store.

Implementation decision update: Razorpay is the candidate provider per the later project direction. India/INR remains provisional. The API records pending orders but does not charge customers.
