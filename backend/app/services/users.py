"""User management helpers."""

from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..models import Role, User


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


async def count_active_admins(db: AsyncSession) -> int:
    """Return the number of active users holding the 'admin' role."""
    result = await db.exec(
        select(User).options(selectinload(User.roles))  # type: ignore[arg-type]
    )
    return sum(1 for u in result.all() if u.active and u.has_role("admin"))


async def ensure_not_last_active_admin(db: AsyncSession, user: User) -> None:
    """Raise 400 if ``user`` is the only remaining active administrator.

    Guards against locking every admin out of the application: called before
    deleting a user, deactivating one, or stripping their admin role.
    """
    if not user.active or not user.has_role("admin"):
        return
    if await count_active_admins(db) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove, deactivate or demote the last active administrator",
        )
