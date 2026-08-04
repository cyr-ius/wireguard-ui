"""Audit log service: record and prune security-relevant actions."""

from __future__ import annotations

from datetime import timedelta

from fastapi import Request
from sqlmodel import delete, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..config import app_settings
from ..models import AuditLog, User, utc_now
from ..proxy import client_ip


async def log_event(
    db: AsyncSession,
    action: str,
    *,
    actor: User | str | None = None,
    target: str | None = None,
    details: str | None = None,
    request: Request | None = None,
    success: bool = True,
) -> None:
    """Insert an audit event and commit it, then prune old/excess events.

    Committed independently of the caller's own transaction so an audit trail
    is recorded even if the caller commits later or the action itself fails.
    """
    actor_username = actor.username if isinstance(actor, User) else actor

    entry = AuditLog(
        action=action,
        actor_username=actor_username,
        target=target,
        details=details,
        ip_address=client_ip(request) if request is not None else None,
        success=success,
    )
    db.add(entry)
    await db.commit()

    await _prune(db)


async def _prune(db: AsyncSession) -> None:
    """Delete audit events beyond the configured retention window or count."""
    cutoff = utc_now() - timedelta(days=app_settings.audit_retention_days)
    await db.exec(delete(AuditLog).where(AuditLog.created_at < cutoff))  # type: ignore[arg-type]

    total = (await db.exec(select(func.count()).select_from(AuditLog))).one()
    excess = total - app_settings.audit_max_events
    if excess > 0:
        oldest_ids = (
            await db.exec(
                select(AuditLog.id).order_by(AuditLog.created_at).limit(excess)  # type: ignore[arg-type]
            )
        ).all()
        if oldest_ids:
            await db.exec(delete(AuditLog).where(AuditLog.id.in_(oldest_ids)))  # type: ignore[union-attr]

    await db.commit()
