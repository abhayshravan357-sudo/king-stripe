"""Initial catalog and order schema."""
from alembic import op
import sqlalchemy as sa

revision = "0001_catalog_orders"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("collections",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("title", sa.String(120), nullable=False), sa.Column("animal", sa.String(60), nullable=False),
        sa.Column("colour", sa.String(60), nullable=False), sa.Column("tagline", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False), sa.Column("status", sa.String(40), nullable=False),
        sa.Column("artwork", sa.String(300), nullable=False), sa.Column("accent", sa.String(20), nullable=False),
        sa.Column("featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("slug", name="uq_collections_slug"))
    op.create_index("ix_collections_slug", "collections", ["slug"], unique=True)
    op.create_table("products",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("name", sa.String(120), nullable=False), sa.Column("garment_type", sa.String(40), nullable=False),
        sa.Column("collection_id", sa.Integer(), sa.ForeignKey("collections.id"), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("slug", name="uq_products_slug"))
    op.create_index("ix_products_slug", "products", ["slug"], unique=True)
    op.create_table("product_variants",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("sku", sa.String(80), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("colour", sa.String(40), nullable=False), sa.Column("size", sa.String(12), nullable=False),
        sa.Column("price_minor", sa.Integer(), nullable=False), sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("product_id", "colour", "size", name="uq_variant_product_colour_size"),
        sa.UniqueConstraint("sku", name="uq_product_variants_sku"))
    op.create_index("ix_product_variants_sku", "product_variants", ["sku"], unique=True)
    op.create_index("ix_product_variants_product_id", "product_variants", ["product_id"])
    op.create_table("orders",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("public_reference", sa.String(40), nullable=False),
        sa.Column("access_token_hash", sa.String(64), nullable=False), sa.Column("status", sa.String(30), nullable=False, server_default="pending_payment"),
        sa.Column("customer_name", sa.String(120), nullable=False), sa.Column("customer_email", sa.String(254), nullable=False),
        sa.Column("shipping_address", sa.Text(), nullable=False), sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("subtotal_minor", sa.Integer(), nullable=False), sa.Column("total_minor", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("public_reference", name="uq_orders_public_reference"))
    op.create_index("ix_orders_public_reference", "orders", ["public_reference"], unique=True)
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_table("order_items",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("variant_id", sa.Integer(), sa.ForeignKey("product_variants.id"), nullable=False),
        sa.Column("product_name", sa.String(120), nullable=False), sa.Column("sku", sa.String(80), nullable=False),
        sa.Column("colour", sa.String(40), nullable=False), sa.Column("size", sa.String(12), nullable=False),
        sa.Column("unit_price_minor", sa.Integer(), nullable=False), sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("line_total_minor", sa.Integer(), nullable=False))
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])


def downgrade():
    raise RuntimeError("Destructive downgrade disabled; restore a verified backup or write a reviewed forward migration")
