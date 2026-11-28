# Improvement backlog

Priorities below reflect release risk, not an assumption that unprovided business rules should be invented.

## Critical — required before paid commerce

- Implement a payment-provider sandbox flow and server-side signature verification; persist explicit payment states and make webhook processing idempotent.
- Define and implement inventory/availability handling, including concurrent checkout behavior.
- Define merchant-approved currency, shipping, tax, returns/refunds, privacy retention and support details.

## High — required before public launch

- Build authenticated, authorized admin order management with an audit trail and secure account bootstrap.
- Add checkout rate limiting, monitoring and operational alerts.
- Select hosting/domain; configure HTTPS, exact CORS origins, managed secrets and database network boundaries.
- Run and document PostgreSQL migration, backup and restore drills in staging.
- Complete Playwright critical journeys and cross-browser/mobile validation.

## Medium — customer confidence and discoverability

- Supply genuine product photographs, garment material/care/fit details and a size guide.
- Publish business-approved shipping, returns/refunds, privacy, terms and contact/support information.
- Add approved product metadata, sitemap, robots policy and canonical/social metadata after production URLs are selected.
- Validate cart behavior when products or variants are removed from the catalog; define persistence and expiration expectations.

## Long-term — only if business needs justify

- Customer accounts, discounts, reviews, order tracking, inventory and sales reporting, and abandoned-cart analysis.

