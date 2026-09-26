"""Add user invitation fields."""

from alembic import op
import sqlalchemy as sa

revision = "0006_add_user_invitation_fields"
down_revision = "0005_add_organizations_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("invitation_token", sa.String(length=255), nullable=True))
    op.add_column(
        "users", sa.Column("invitation_sent_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "users",
        sa.Column("invitation_accepted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f("ix_users_invitation_token"), "users", ["invitation_token"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_invitation_token"), table_name="users")
    op.drop_column("users", "invitation_accepted_at")
    op.drop_column("users", "invitation_sent_at")
    op.drop_column("users", "invitation_token")
