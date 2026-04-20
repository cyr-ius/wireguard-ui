"""Alembic sync migration environment for SQLModel."""

import os
import sys
from logging.config import fileConfig

# Ensure `app` package is importable regardless of the working directory
# (uvicorn runs from /app, but `from app.config import ...` needs /app/backend in sys.path)
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from sqlalchemy import create_engine
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
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_engine(get_url(), poolclass=NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
