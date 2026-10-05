"""Add task cost and completion tracking fields."""

from alembic import op
import sqlalchemy as sa

revision = "0012_add_task_cost_tracking"
down_revision = "0011_add_task_workflows"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("estimated_cost", sa.Numeric(10, 2), nullable=True))
    op.add_column("tasks", sa.Column("actual_cost", sa.Numeric(10, 2), nullable=True))
    op.add_column("tasks", sa.Column("completion_notes", sa.Text(), nullable=True))
    op.add_column("tasks", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("tasks", "completed_at")
    op.drop_column("tasks", "completion_notes")
    op.drop_column("tasks", "actual_cost")
    op.drop_column("tasks", "estimated_cost")
