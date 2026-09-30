"""Expand operations workflows for notifications, reminders and documents."""

from alembic import op
import sqlalchemy as sa

revision = "0007_expand_operations_workflows"
down_revision = "0006_add_user_invitation_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("invitation_delivery_status", sa.String(length=50), nullable=False, server_default="pending"))
    op.add_column("users", sa.Column("invitation_delivery_error", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("invitation_last_attempt_at", sa.DateTime(timezone=True), nullable=True))

    op.add_column("invoices", sa.Column("due_date", sa.Date(), nullable=True))

    op.add_column("documents", sa.Column("category", sa.String(length=100), nullable=True))
    op.add_column("documents", sa.Column("version_label", sa.String(length=100), nullable=True))
    op.add_column("documents", sa.Column("review_status", sa.String(length=50), nullable=False, server_default="pending"))
    op.add_column("documents", sa.Column("review_notes", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("documents", sa.Column("reviewed_by", sa.String(length=36), nullable=True))

    op.create_table(
        "payment_reminders",
        sa.Column("invoice_id", sa.String(length=36), nullable=False),
        sa.Column("recipient_email", sa.String(length=255), nullable=False),
        sa.Column("reminder_level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivery_error", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payment_reminders_invoice_id"), "payment_reminders", ["invoice_id"], unique=False)
    op.create_index(op.f("ix_payment_reminders_organization_id"), "payment_reminders", ["organization_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_payment_reminders_organization_id"), table_name="payment_reminders")
    op.drop_index(op.f("ix_payment_reminders_invoice_id"), table_name="payment_reminders")
    op.drop_table("payment_reminders")

    op.drop_column("documents", "reviewed_by")
    op.drop_column("documents", "reviewed_at")
    op.drop_column("documents", "review_notes")
    op.drop_column("documents", "review_status")
    op.drop_column("documents", "version_label")
    op.drop_column("documents", "category")

    op.drop_column("invoices", "due_date")

    op.drop_column("users", "invitation_last_attempt_at")
    op.drop_column("users", "invitation_delivery_error")
    op.drop_column("users", "invitation_delivery_status")
