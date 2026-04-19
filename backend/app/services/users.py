"""User management helpers."""

from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..models import Role


async def load_roles(db: AsyncSession, role_ids: list[int]) -> list[Role]:
    """Load Role objects by ID list, raising 400 if the list is empty."""
    if not role_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Role is required"
        )

    result = await db.exec(select(Role).where(Role.id.in_(role_ids)))
    roles = result.all()
    role_by_id = {r.id: r for r in roles if r.id is not None}
    return [role_by_id[rid] for rid in role_ids if rid in role_by_id]
