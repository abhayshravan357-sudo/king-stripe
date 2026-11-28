# Decision log

- 2026-11-27: Use a single FastAPI modular monolith, SQLAlchemy/Alembic, and PostgreSQL as requested. Keep the existing static storefront and assets.
- 2026-11-27: INR is provisional; catalog values are stored as paise (`display rupees × 100`) pending merchant confirmation.
- 2026-11-27: Razorpay is the candidate provider per user direction. Payments stay disabled without explicit live activation authorization and credentials. Current checkout can persist a pending order only.
- 2026-11-27: Do not add shipping, tax, inventory counts, refunds, delivery promises, or legal copy without business policy. Product stock is not represented as available quantity.
- 2026-11-27: Keep catalog concepts visible, matching the current frontend labels; only six existing Tiger × Black products are created.
- 2026-11-27: Do not create admin credentials or a publicly callable admin interface until a secure bootstrap/operating method is selected. No admin route currently exists.
- 2026-11-27: The local Compose API binds only to loopback; database port is not exposed to the host.
