"""Initial schema — users and build_jobs tables

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-26 00:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id",              sa.Integer(),     primary_key=True),
        sa.Column("username",        sa.String(200),   nullable=False),
        sa.Column("hashed_password", sa.String(200),   nullable=False),
        sa.Column("role",            sa.String(30),    nullable=False, server_default="viewer"),
        sa.Column("tenant_id",       sa.String(120),   nullable=False, server_default="default-tenant"),
        sa.Column("is_active",       sa.Boolean(),     nullable=False, server_default="1"),
        sa.Column("created_at",      sa.DateTime(),    nullable=False),
    )
    op.create_index("ix_users_username",  "users", ["username"],  unique=True)
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"], unique=False)

    # ── build_jobs ─────────────────────────────────────────────────────────────
    op.create_table(
        "build_jobs",
        sa.Column("id",           sa.Integer(),  primary_key=True),
        sa.Column("status",       sa.String(30), nullable=False, server_default="queued"),
        sa.Column("request_json", sa.Text(),     nullable=False, server_default="{}"),
        sa.Column("result_json",  sa.Text(),     nullable=True),
        sa.Column("error_msg",    sa.Text(),     nullable=True),
        sa.Column("tenant_id",    sa.String(120), nullable=False, server_default="default-tenant"),
        sa.Column("created_at",   sa.DateTime(), nullable=False),
        sa.Column("updated_at",   sa.DateTime(), nullable=False),
    )
    op.create_index("ix_build_jobs_tenant_id", "build_jobs", ["tenant_id"])
    op.create_index("ix_build_jobs_status",    "build_jobs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_build_jobs_status",    table_name="build_jobs")
    op.drop_index("ix_build_jobs_tenant_id", table_name="build_jobs")
    op.drop_table("build_jobs")

    op.drop_index("ix_users_tenant_id", table_name="users")
    op.drop_index("ix_users_username",  table_name="users")
    op.drop_table("users")
