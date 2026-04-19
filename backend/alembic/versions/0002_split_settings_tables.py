"""split oidc and smtp settings into dedicated tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-19
"""

import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "oidc_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("oidc_only", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("issuer", sa.String(length=512), nullable=False, server_default=""),
        sa.Column(
            "client_id", sa.String(length=255), nullable=False, server_default=""
        ),
        sa.Column(
            "client_secret", sa.String(length=512), nullable=False, server_default=""
        ),
        sa.Column(
            "redirect_uri", sa.String(length=512), nullable=False, server_default=""
        ),
        sa.Column(
            "post_logout_redirect_uri",
            sa.String(length=512),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "response_type", sa.String(length=50), nullable=False, server_default="code"
        ),
        sa.Column(
            "scope",
            sa.String(length=255),
            nullable=False,
            server_default="openid profile email",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "smtp_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("server", sa.String(length=255), nullable=True),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("password", sa.String(length=255), nullable=True),
        sa.Column("from_address", sa.String(length=255), nullable=True),
        sa.Column(
            "from_name",
            sa.String(length=255),
            nullable=False,
            server_default="WireGuard UI",
        ),
        sa.Column("tls", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("ssl", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("verify", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column(
            "default_language", sa.String(length=5), nullable=False, server_default="en"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Migrate existing data from global_settings (if any row exists)
    op.execute("""
        INSERT INTO oidc_settings (
            enabled, oidc_only, issuer, client_id, client_secret,
            redirect_uri, post_logout_redirect_uri, response_type, scope
        )
        SELECT
            COALESCE(oidc_enabled, 0),
            COALESCE(oidc_only, 0),
            COALESCE(oidc_issuer, ''),
            COALESCE(oidc_client_id, ''),
            COALESCE(oidc_client_secret, ''),
            COALESCE(oidc_redirect_uri, ''),
            COALESCE(oidc_post_logout_redirect_uri, ''),
            COALESCE(oidc_response_type, 'code'),
            COALESCE(oidc_scope, 'openid profile email')
        FROM global_settings
    """)

    op.execute("""
        INSERT INTO smtp_settings (
            server, port, username, password, from_address, from_name,
            tls, ssl, verify, default_language
        )
        SELECT
            smtp_server,
            smtp_port,
            smtp_username,
            smtp_password,
            smtp_from,
            COALESCE(smtp_from_name, 'WireGuard UI'),
            COALESCE(smtp_tls, 1),
            COALESCE(smtp_ssl, 0),
            COALESCE(smtp_verify, 1),
            COALESCE(default_email_language, 'en')
        FROM global_settings
    """)

    # Drop OIDC and SMTP columns from global_settings using batch mode (SQLite compat)
    oidc_cols = [
        "oidc_enabled",
        "oidc_only",
        "oidc_issuer",
        "oidc_client_id",
        "oidc_client_secret",
        "oidc_redirect_uri",
        "oidc_post_logout_redirect_uri",
        "oidc_response_type",
        "oidc_scope",
    ]
    smtp_cols = [
        "smtp_server",
        "smtp_port",
        "smtp_username",
        "smtp_password",
        "smtp_from",
        "smtp_from_name",
        "smtp_tls",
        "smtp_ssl",
        "smtp_verify",
        "default_email_language",
    ]

    with op.batch_alter_table("global_settings") as batch_op:
        for col in oidc_cols + smtp_cols:
            batch_op.drop_column(col)


def downgrade() -> None:
    with op.batch_alter_table("global_settings") as batch_op:
        batch_op.add_column(sa.Column("oidc_enabled", sa.Boolean(), server_default="0"))
        batch_op.add_column(sa.Column("oidc_only", sa.Boolean(), server_default="0"))
        batch_op.add_column(sa.Column("oidc_issuer", sa.String(512)))
        batch_op.add_column(sa.Column("oidc_client_id", sa.String(255)))
        batch_op.add_column(sa.Column("oidc_client_secret", sa.String(512)))
        batch_op.add_column(sa.Column("oidc_redirect_uri", sa.String(512)))
        batch_op.add_column(sa.Column("oidc_post_logout_redirect_uri", sa.String(512)))
        batch_op.add_column(
            sa.Column("oidc_response_type", sa.String(50), server_default="code")
        )
        batch_op.add_column(sa.Column("oidc_scope", sa.String(255)))
        batch_op.add_column(sa.Column("smtp_server", sa.String(255)))
        batch_op.add_column(sa.Column("smtp_port", sa.Integer()))
        batch_op.add_column(sa.Column("smtp_username", sa.String(255)))
        batch_op.add_column(sa.Column("smtp_password", sa.String(255)))
        batch_op.add_column(sa.Column("smtp_from", sa.String(255)))
        batch_op.add_column(
            sa.Column("smtp_from_name", sa.String(255), server_default="WireGuard UI")
        )
        batch_op.add_column(sa.Column("smtp_tls", sa.Boolean(), server_default="1"))
        batch_op.add_column(sa.Column("smtp_ssl", sa.Boolean(), server_default="0"))
        batch_op.add_column(sa.Column("smtp_verify", sa.Boolean(), server_default="1"))
        batch_op.add_column(
            sa.Column("default_email_language", sa.String(5), server_default="en")
        )

    op.execute("""
        UPDATE global_settings SET
            oidc_enabled = (SELECT enabled FROM oidc_settings LIMIT 1),
            oidc_only = (SELECT oidc_only FROM oidc_settings LIMIT 1),
            oidc_issuer = (SELECT issuer FROM oidc_settings LIMIT 1),
            oidc_client_id = (SELECT client_id FROM oidc_settings LIMIT 1),
            oidc_client_secret = (SELECT client_secret FROM oidc_settings LIMIT 1),
            oidc_redirect_uri = (SELECT redirect_uri FROM oidc_settings LIMIT 1),
            oidc_post_logout_redirect_uri = (SELECT post_logout_redirect_uri FROM oidc_settings LIMIT 1),
            oidc_response_type = (SELECT response_type FROM oidc_settings LIMIT 1),
            oidc_scope = (SELECT scope FROM oidc_settings LIMIT 1),
            smtp_server = (SELECT server FROM smtp_settings LIMIT 1),
            smtp_port = (SELECT port FROM smtp_settings LIMIT 1),
            smtp_username = (SELECT username FROM smtp_settings LIMIT 1),
            smtp_password = (SELECT password FROM smtp_settings LIMIT 1),
            smtp_from = (SELECT from_address FROM smtp_settings LIMIT 1),
            smtp_from_name = (SELECT from_name FROM smtp_settings LIMIT 1),
            smtp_tls = (SELECT tls FROM smtp_settings LIMIT 1),
            smtp_ssl = (SELECT ssl FROM smtp_settings LIMIT 1),
            smtp_verify = (SELECT verify FROM smtp_settings LIMIT 1),
            default_email_language = (SELECT default_language FROM smtp_settings LIMIT 1)
    """)

    op.drop_table("smtp_settings")
    op.drop_table("oidc_settings")
