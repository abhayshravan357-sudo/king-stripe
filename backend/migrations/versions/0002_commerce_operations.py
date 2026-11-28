"""Idempotency, payment inbox, admin sessions/audit, and inventory tables."""
from alembic import op
import sqlalchemy as sa

revision = "0002_commerce_operations"
down_revision = "0001_catalog_orders"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("orders", sa.Column("fulfillment_status", sa.String(30), nullable=False, server_default="unfulfilled"))
    op.add_column("orders", sa.Column("idempotency_key_hash", sa.String(64), nullable=True))
    op.add_column("orders", sa.Column("request_fingerprint", sa.String(64), nullable=True))
    op.add_column("orders", sa.Column("provider_order_id", sa.String(80), nullable=True))
    op.add_column("orders", sa.Column("provider_payment_id", sa.String(80), nullable=True))
    op.add_column("orders", sa.Column("refunded_minor", sa.Integer(), nullable=False, server_default="0"))
    op.create_index("ix_orders_fulfillment_status", "orders", ["fulfillment_status"])
    op.create_index("ix_orders_idempotency_key_hash", "orders", ["idempotency_key_hash"], unique=True)
    op.create_index("uq_orders_provider_order_id", "orders", ["provider_order_id"], unique=True)
    op.create_index("uq_orders_provider_payment_id", "orders", ["provider_payment_id"], unique=True)
    op.create_table("payment_events",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("provider_event_id", sa.String(120), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False), sa.Column("payload_sha256", sa.String(64), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True), sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("provider_event_id", name="uq_payment_events_provider_event_id"))
    op.create_index("ix_payment_events_provider_event_id", "payment_events", ["provider_event_id"], unique=True)
    op.create_table("inventory_records",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("variant_id", sa.Integer(), sa.ForeignKey("product_variants.id"), nullable=False),
        sa.Column("mode", sa.String(24), nullable=False), sa.Column("quantity_on_hand", sa.Integer(), nullable=True),
        sa.Column("quantity_reserved", sa.Integer(), nullable=False, server_default="0"), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("variant_id", name="uq_inventory_records_variant_id"))
    op.create_index("ix_inventory_records_variant_id", "inventory_records", ["variant_id"], unique=True)
    op.create_table("inventory_reservations",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("variant_id", sa.Integer(), sa.ForeignKey("product_variants.id"), nullable=False), sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="reserved"), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("order_id", "variant_id", name="uq_reservation_order_variant"))
    op.create_index("ix_inventory_reservations_order_id", "inventory_reservations", ["order_id"])
    op.create_index("ix_inventory_reservations_variant_id", "inventory_reservations", ["variant_id"])
    op.create_table("inventory_movements",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("variant_id", sa.Integer(), sa.ForeignKey("product_variants.id"), nullable=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=True), sa.Column("quantity_delta", sa.Integer(), nullable=False),
        sa.Column("movement_type", sa.String(24), nullable=False), sa.Column("actor", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_inventory_movements_variant_id", "inventory_movements", ["variant_id"])
    op.create_index("ix_inventory_movements_order_id", "inventory_movements", ["order_id"])
    op.create_table("admin_sessions",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("token_sha256", sa.String(64), nullable=False),
        sa.Column("csrf_sha256", sa.String(64), nullable=False), sa.Column("username", sa.String(120), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("token_sha256", name="uq_admin_sessions_token_sha256"))
    op.create_index("ix_admin_sessions_token_sha256", "admin_sessions", ["token_sha256"], unique=True)
    op.create_index("ix_admin_sessions_expires_at", "admin_sessions", ["expires_at"])
    op.create_table("admin_audit",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("username", sa.String(120), nullable=False),
        sa.Column("action", sa.String(80), nullable=False), sa.Column("resource_type", sa.String(40), nullable=False),
        sa.Column("resource_id", sa.String(120), nullable=False), sa.Column("details", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))


def downgrade():
    raise RuntimeError("Destructive downgrade disabled; restore a verified backup or write a reviewed forward migration")
