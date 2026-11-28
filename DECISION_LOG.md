# Decision log

Updated: 2026-11-27

- Keep public checkout pending when payment is disabled; never represent a pending order as paid.
- Use Razorpay behind a provider interface for the initial INR integration. Test mode is the only supported mode without an explicit future live-payment activation; `ALLOW_LIVE_PAYMENTS=false` by default.
- Keep inventory behavior configurable (`limited`, `preorder`, `made_to_order`, `unlimited`) and default it to disabled. No quantities or sales policy are assumed.
- Keep admin registration closed. Provision the first operator through environment configuration with a locally generated PBKDF2 password hash.
- Keep the API bound to loopback in laptop Compose. No public tunnel, paid service, domain, or public deployment was activated.
- Store customer address/contact only on the order and return it only through authenticated admin detail; public order lookup returns status and totals with a bearer access token.
- Do not guess shipping, tax, delivery, cancellation, refund/return, privacy, or customer-support policies.
