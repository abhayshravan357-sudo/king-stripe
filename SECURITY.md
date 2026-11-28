# Security notes

- Payment defaults to disabled and live activation defaults off. The API supports Razorpay test/live configuration, but only enable an approved sandbox account for testing; never infer paid status from a browser redirect.
- Checkout prices are calculated server-side. Orders use random public references and a scoped access token whose hash is stored. Reuse the same idempotency key when retrying a checkout request.
- Admin access uses a configured password hash, expiring session cookies, CSRF validation on mutations, login throttling and audit events. Provision credentials through the documented local process; do not commit secrets.
- CORS uses an explicit origin allowlist and credentials for the admin session flow. Production must set only the HTTPS storefront origin. Basic response security headers are configured; add deployment-specific HTTPS/HSTS, CSP, firewall, monitoring and secret-manager controls before launch.
- The in-process rate limiter is suitable only for a single local API process. Public multi-worker deployments need shared or edge rate limiting and abuse monitoring.
- Customer name, email and delivery address are stored with orders. Define approved access, retention, deletion and privacy practices before taking real orders.
- Inventory mode defaults to disabled and no stock quantities are invented. Choose a policy and enter accurate per-variant stock before accepting orders.
- The local Compose API binds to loopback and PostgreSQL has no published host port. Do not expose the laptop or use real customer data for testing.
- Backup and restore helpers avoid displaying database credentials; restore refuses the active database and non-empty targets. A real PostgreSQL recovery drill is still required.
- Automated checks are not a complete security review. Review [SECURITY_AUDIT.md](SECURITY_AUDIT.md) and [KING_STRIPE_FINAL_PRODUCTION_REPORT.md](KING_STRIPE_FINAL_PRODUCTION_REPORT.md) for scope and open launch gates.
