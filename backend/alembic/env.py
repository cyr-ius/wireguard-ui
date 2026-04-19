"""Alembic sync migration environment for SQLModel."""

import os
import sys
from logging.config import fileConfig

# Ensure `app` package is importable regardless of the working directory
# (uvicorn runs from /app, but `from app.config import ...` needs /app/backend in sys.path)
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect as sa_inspect
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def get_url() -> str:
    from app.config import app_settings

    url = app_settings.db_path
    # Convert async URL to sync for Alembic (aiosqlite → sqlite)
    return url.replace("sqlite+aiosqlite://", "sqlite://")


def _stamp_if_unversioned(conn) -> bool:
    """Stamp pre-Alembic databases as head without running DDL."""
    inspector = sa_inspect(conn)
    if inspector.has_table("users") and not inspector.has_table("alembic_version"):
        script = ScriptDirectory.from_config(config)
        MigrationContext.configure(conn).stamp(script, "head")
        return True
    return False


def run_migrations_offline() -> None:
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(get_url(), poolclass=NullPool)
    with engine.connect() as conn:
        if not _stamp_if_unversioned(conn):
            context.configure(connection=conn, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
        conn.commit()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
