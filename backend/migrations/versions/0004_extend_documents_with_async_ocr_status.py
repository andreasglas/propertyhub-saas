"""Extend documents with async OCR status details."""

from alembic import op
import sqlalchemy as sa

revision = "0004_extend_documents_with_async_ocr_status"
down_revision = "0003_extend_documents_with_ocr"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("ocr_error", sa.Text(), nullable=True))
    op.add_column(
        "documents",
        sa.Column("ocr_attempt_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "documents",
        sa.Column("ocr_started_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("documents", "ocr_started_at")
    op.drop_column("documents", "ocr_attempt_count")
    op.drop_column("documents", "ocr_error")
