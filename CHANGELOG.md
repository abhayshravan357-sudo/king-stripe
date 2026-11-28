# Changelog

## 2026-11-27

- Added FastAPI application foundation, PostgreSQL models, Alembic migration setup, local Docker Compose, API health/catalog endpoints, and a pending-order flow that recalculates prices on the server.
- Connected the existing storefront to load catalog data and submit pending orders when the local API is available. Existing preview behavior remains as offline fallback.
- Added backend API tests and local deployment/backup documentation. Payment, admin operations, and public deployment remain disabled/pending.
