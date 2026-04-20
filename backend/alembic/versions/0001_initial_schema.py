"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-19
"""

import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("permissions", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "auth_source", sa.String(length=20), nullable=False, server_default="local"
        ),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("fs_uniquifier", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fs_uniquifier"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_fs_uniquifier", "users", ["fs_uniquifier"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

    op.create_table(
        "wg_server",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("address", sa.String(length=50), nullable=False),
        sa.Column("listen_port", sa.Integer(), nullable=False),
        sa.Column("private_key", sa.String(length=255), nullable=False),
        sa.Column("public_key", sa.String(length=255), nullable=False),
        sa.Column("postup", sa.Text(), nullable=True),
        sa.Column("postdown", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "wg_clients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("public_key", sa.String(length=255), nullable=False),
        sa.Column("private_key", sa.String(length=255), nullable=False),
        sa.Column("preshared_key", sa.String(), nullable=True),
        sa.Column("allocated_ips", sa.String(length=255), nullable=False),
        sa.Column("allowed_ips", sa.JSON(), nullable=True),
        sa.Column("use_server_dns", sa.Boolean(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_wg_clients_email", "wg_clients", ["email"], unique=True)
    op.create_index("ix_wg_clients_name", "wg_clients", ["name"], unique=True)

    op.create_table(
        "global_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("endpoint_address", sa.String(length=255), nullable=True),
        sa.Column("dns_servers", sa.JSON(), nullable=True),
        sa.Column("mtu", sa.Integer(), nullable=True),
        sa.Column("persistent_keepalive", sa.Integer(), nullable=True),
        sa.Column("maintenance_mode", sa.Boolean(), nullable=False),
        sa.Column("default_email_language", sa.String(length=5), nullable=False),
        sa.Column("oidc_enabled", sa.Boolean(), nullable=False),
        sa.Column("oidc_only", sa.Boolean(), nullable=False),
        sa.Column("oidc_issuer", sa.String(length=512), nullable=True),
        sa.Column("oidc_client_id", sa.String(length=255), nullable=True),
        sa.Column("oidc_client_secret", sa.String(length=512), nullable=True),
        sa.Column("oidc_redirect_uri", sa.String(length=512), nullable=True),
        sa.Column(
            "oidc_post_logout_redirect_uri", sa.String(length=512), nullable=True
        ),
        sa.Column("oidc_response_type", sa.String(length=50), nullable=True),
        sa.Column("oidc_scope", sa.String(length=255), nullable=True),
        sa.Column("smtp_server", sa.String(length=255), nullable=True),
        sa.Column("smtp_port", sa.Integer(), nullable=True),
        sa.Column("smtp_username", sa.String(length=255), nullable=True),
        sa.Column("smtp_password", sa.String(length=255), nullable=True),
        sa.Column("smtp_from", sa.String(length=255), nullable=True),
        sa.Column("smtp_from_name", sa.String(length=255), nullable=False),
        sa.Column("smtp_tls", sa.Boolean(), nullable=False),
        sa.Column("smtp_ssl", sa.Boolean(), nullable=False),
        sa.Column("smtp_verify", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("global_settings")
    op.drop_index("ix_wg_clients_name", table_name="wg_clients")
    op.drop_index("ix_wg_clients_email", table_name="wg_clients")
    op.drop_table("wg_clients")
    op.drop_table("wg_server")
    op.drop_table("user_roles")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_fs_uniquifier", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_index("ix_roles_name", table_name="roles")
    op.drop_table("roles")
