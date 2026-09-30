"""Add operating cost periods and items."""

from alembic import op
import sqlalchemy as sa

revision = "0009_add_operating_costs"
down_revision = "0008_add_audit_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "operating_cost_periods",
        sa.Column("property_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_operating_cost_periods_organization_id"), "operating_cost_periods", ["organization_id"], unique=False)
    op.create_index(op.f("ix_operating_cost_periods_property_id"), "operating_cost_periods", ["property_id"], unique=False)

    op.create_table(
        "operating_cost_items",
        sa.Column("period_id", sa.String(length=36), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("allocation_method", sa.String(length=50), nullable=False, server_default="area"),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("billable", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["period_id"], ["operating_cost_periods.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_operating_cost_items_organization_id"), "operating_cost_items", ["organization_id"], unique=False)
    op.create_index(op.f("ix_operating_cost_items_period_id"), "operating_cost_items", ["period_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_operating_cost_items_period_id"), table_name="operating_cost_items")
    op.drop_index(op.f("ix_operating_cost_items_organization_id"), table_name="operating_cost_items")
    op.drop_table("operating_cost_items")
    op.drop_index(op.f("ix_operating_cost_periods_property_id"), table_name="operating_cost_periods")
    op.drop_index(op.f("ix_operating_cost_periods_organization_id"), table_name="operating_cost_periods")
    op.drop_table("operating_cost_periods")
