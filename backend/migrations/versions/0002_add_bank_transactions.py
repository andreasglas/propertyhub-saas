"""Add bank transactions for banking imports."""

from alembic import op
import sqlalchemy as sa

revision = "0002_add_bank_transactions"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bank_transactions",
        sa.Column("payment_id", sa.String(length=36), nullable=True),
        sa.Column("external_id", sa.String(length=100), nullable=True),
        sa.Column("account_name", sa.String(length=100), nullable=False),
        sa.Column("transaction_type", sa.String(length=50), nullable=False),
        sa.Column("booking_date", sa.Date(), nullable=True),
        sa.Column("value_date", sa.Date(), nullable=True),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("counterparty_name", sa.String(length=255), nullable=True),
        sa.Column("iban", sa.String(length=34), nullable=True),
        sa.Column("reference", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_bank_transactions_external_id"),
        "bank_transactions",
        ["external_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_bank_transactions_organization_id"),
        "bank_transactions",
        ["organization_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_bank_transactions_organization_id"),
        table_name="bank_transactions",
    )
    op.drop_index(
        op.f("ix_bank_transactions_external_id"),
        table_name="bank_transactions",
    )
    op.drop_table("bank_transactions")
