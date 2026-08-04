"""Audit log router — read-only, admin only."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..auth import get_current_admin
from ..database import get_db
from ..models import AuditLog, User
from ..schemas import AuditLogPage

router = APIRouter()


@router.get("", response_model=AuditLogPage)
async def list_audit_events(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    action: str | None = Query(default=None),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AuditLogPage:
    """Return paginated audit log entries, most recent first."""
    query = select(AuditLog)
    count_query = select(func.count()).select_from(AuditLog)
    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)

    total = (await db.exec(count_query)).one()
    items = (
        await db.exec(
            query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)  # type: ignore[attr-defined]
        )
    ).all()

    return AuditLogPage(items=list(items), total=total)
