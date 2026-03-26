"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-26

SECURITY NOTE: The audit_logs table is append-only. The application DB user
must NOT be granted UPDATE or DELETE privileges on this table. Enforce at the
DB role level in production:
    REVOKE UPDATE, DELETE ON TABLE audit_logs FROM <app_db_user>;
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("plan", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("plone_username", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.CheckConstraint("role IN ('admin', 'member', 'guest')", name="ck_users_role"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plone_username", "tenant_id", name="uq_users_plone_username_tenant"),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])

    op.create_table(
        "tenant_plugins",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plugin_name", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tenant_plugins_tenant_plugin", "tenant_plugins", ["tenant_id", "plugin_name"])

    op.create_table(
        "tenant_token_quota",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("max_tokens", sa.Integer(), nullable=False),
        sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reset_date", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("tenant_id"),
    )

    # APPEND ONLY — REVOKE UPDATE, DELETE from app user in production
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("resource", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_tenant_timestamp", "audit_logs", ["tenant_id", "timestamp"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_tenant_timestamp", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_table("tenant_token_quota")
    op.drop_index("ix_tenant_plugins_tenant_plugin", table_name="tenant_plugins")
    op.drop_table("tenant_plugins")
    op.drop_index("ix_users_tenant_id", table_name="users")
    op.drop_table("users")
    op.drop_table("tenants")
