"""Alembic async migration environment for SQLModel."""

import asyncio
from logging.config import fileConfig

from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from alembic import context
from app import models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def get_url() -> str:
    from app.config import app_settings

    return app_settings.db_path


def _stamp_if_unversioned(sync_conn) -> bool:
    """Stamp pre-Alembic databases as head without running DDL."""
    inspector = sa_inspect(sync_conn)
    if inspector.has_table("users") and not inspector.has_table("alembic_version"):
        script = ScriptDirectory.from_config(config)
        MigrationContext.configure(sync_conn).stamp(script, "head")
        return True
    return False


def _run_migrations(sync_conn) -> None:
    context.configure(connection=sync_conn, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def _run_async_migrations() -> None:
    engine = create_async_engine(get_url(), poolclass=NullPool)
    async with engine.connect() as conn:
        stamped = await conn.run_sync(_stamp_if_unversioned)
        if not stamped:
            await conn.run_sync(_run_migrations)
        await conn.commit()
    await engine.dispose()


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
    asyncio.run(_run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
