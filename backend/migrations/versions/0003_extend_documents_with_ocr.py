"""Extend documents with OCR metadata."""

from alembic import op
import sqlalchemy as sa

revision = "0003_extend_documents_with_ocr"
down_revision = "0002_add_bank_transactions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("ocr_status", sa.String(length=50), nullable=False, server_default="pending"),
    )
    op.add_column("documents", sa.Column("ocr_result", sa.JSON(), nullable=True))
    op.add_column(
        "documents",
        sa.Column("ocr_processed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("documents", "ocr_processed_at")
    op.drop_column("documents", "ocr_result")
    op.drop_column("documents", "ocr_status")
