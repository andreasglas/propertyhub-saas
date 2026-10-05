"""Add vendor and task workflow tables."""

from alembic import op
import sqlalchemy as sa

revision = "0011_add_task_workflows"
down_revision = "0010_add_tasks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vendors",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("service_type", sa.String(length=100), nullable=False, server_default="maintenance"),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("contact_phone", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vendors_organization_id"), "vendors", ["organization_id"], unique=False)

    op.create_table(
        "task_comments",
        sa.Column("task_id", sa.String(length=36), nullable=False),
        sa.Column("author_user_id", sa.String(length=36), nullable=True),
        sa.Column("author_email", sa.String(length=255), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_comments_organization_id"), "task_comments", ["organization_id"], unique=False)
    op.create_index(op.f("ix_task_comments_task_id"), "task_comments", ["task_id"], unique=False)

    op.create_table(
        "task_templates",
        sa.Column("property_id", sa.String(length=36), nullable=True),
        sa.Column("unit_id", sa.String(length=36), nullable=True),
        sa.Column("vendor_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="maintenance"),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("recurrence_frequency", sa.String(length=20), nullable=False, server_default="monthly"),
        sa.Column("next_due_date", sa.Date(), nullable=False),
        sa.Column("assignee_name", sa.String(length=255), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"]),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_templates_organization_id"), "task_templates", ["organization_id"], unique=False)
    op.create_index(op.f("ix_task_templates_property_id"), "task_templates", ["property_id"], unique=False)
    op.create_index(op.f("ix_task_templates_unit_id"), "task_templates", ["unit_id"], unique=False)
    op.create_index(op.f("ix_task_templates_vendor_id"), "task_templates", ["vendor_id"], unique=False)

    op.add_column("tasks", sa.Column("vendor_id", sa.String(length=36), nullable=True))
    op.add_column("tasks", sa.Column("recurring_template_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(None, "tasks", "vendors", ["vendor_id"], ["id"])
    op.create_foreign_key(None, "tasks", "task_templates", ["recurring_template_id"], ["id"])
    op.create_index(op.f("ix_tasks_vendor_id"), "tasks", ["vendor_id"], unique=False)
    op.create_index(op.f("ix_tasks_recurring_template_id"), "tasks", ["recurring_template_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tasks_recurring_template_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_vendor_id"), table_name="tasks")
    op.drop_constraint(None, "tasks", type_="foreignkey")
    op.drop_constraint(None, "tasks", type_="foreignkey")
    op.drop_column("tasks", "recurring_template_id")
    op.drop_column("tasks", "vendor_id")

    op.drop_index(op.f("ix_task_templates_vendor_id"), table_name="task_templates")
    op.drop_index(op.f("ix_task_templates_unit_id"), table_name="task_templates")
    op.drop_index(op.f("ix_task_templates_property_id"), table_name="task_templates")
    op.drop_index(op.f("ix_task_templates_organization_id"), table_name="task_templates")
    op.drop_table("task_templates")

    op.drop_index(op.f("ix_task_comments_task_id"), table_name="task_comments")
    op.drop_index(op.f("ix_task_comments_organization_id"), table_name="task_comments")
    op.drop_table("task_comments")

    op.drop_index(op.f("ix_vendors_organization_id"), table_name="vendors")
    op.drop_table("vendors")
