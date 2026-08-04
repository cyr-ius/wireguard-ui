"""User management router — admin only."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..auth import get_current_admin, hash_password
from ..database import get_db
from ..models import Role, User
from ..schemas import RoleResponse, UserCreate, UserResponse, UserUpdate
from ..services.audit import log_event
from ..services.users import (
    count_active_admins,
    ensure_not_last_active_admin,
    load_roles,
)

router = APIRouter()


@router.get("", response_model=list[UserResponse])
async def list_users(
    _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
):
    """Return all users ordered by username."""
    result = await db.exec(
        select(User).options(selectinload(User.roles)).order_by(User.username)  # type: ignore[arg-type]
    )
    return result.all()


@router.get("/utils/roles", response_model=list[RoleResponse])
async def list_roles(
    _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
):
    """Return all available roles."""
    result = await db.exec(select(Role).order_by(Role.name))
    return result.all()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    request: Request,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user with hashed password and assigned roles."""
    for field, value, msg in [
        (User.username, data.username, "Username already in use"),
        (User.email, data.email, "Email already in use"),
    ]:
        if (await db.exec(select(User).where(field == value))).one_or_none():
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)

    payload = data.model_dump(exclude={"password", "role_ids"})
    payload["hashed_password"] = hash_password(data.password)
    user = User.model_validate(payload)
    user.roles = await load_roles(db, data.role_ids)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    result = await db.exec(
        select(User).where(User.id == user.id).options(selectinload(User.roles))  # type: ignore[arg-type]
    )
    created = result.one()
    await log_event(
        db,
        "user.created",
        actor=current_admin,
        target=f"user:{created.username}",
        request=request,
    )
    return created


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Return a single user by ID."""
    u = (
        await db.exec(
            select(User).where(User.id == user_id).options(selectinload(User.roles))  # type: ignore[arg-type]
        )
    ).one_or_none()
    if not u:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    return u


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    request: Request,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Partially update a user's profile and roles."""
    u = (
        await db.exec(
            select(User).where(User.id == user_id).options(selectinload(User.roles))  # type: ignore[arg-type]
        )
    ).one_or_none()
    if not u:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")

    payload = data.model_dump(exclude_unset=True)

    # Identity fields and password of externally managed (OIDC) accounts are
    # owned by the identity provider; only local authorization (roles, active
    # status) may be changed here.
    if u.auth_source != "local":
        managed_fields = {"email", "first_name", "last_name", "password"}
        if managed_fields & payload.keys():
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Email, name and password of externally managed accounts "
                    "cannot be changed here"
                ),
            )

    if "email" in payload and payload["email"] != u.email:
        if (
            await db.exec(select(User).where(User.email == payload["email"]))
        ).one_or_none():
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Email already in use"
            )

    new_roles = (
        await load_roles(db, payload["role_ids"]) if "role_ids" in payload else None
    )

    # Guard against locking every admin out: block deactivating or demoting
    # this user if they are currently the last active administrator.
    was_active_admin = u.active and u.has_role("admin")
    if was_active_admin:
        will_be_active = payload.get("active", u.active)
        will_be_admin = (
            any(r.name == "admin" for r in new_roles) if new_roles is not None else True
        )
        if (
            not (will_be_active and will_be_admin)
            and await count_active_admins(db) <= 1
        ):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate or demote the last active administrator",
            )

    if new_roles is not None:
        u.roles = new_roles
        payload.pop("role_ids")

    new_password = payload.pop("password", None)
    if new_password:
        if len(new_password) < 8:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Password must be at least 8 characters",
            )
        u.hashed_password = hash_password(new_password)

    u.sqlmodel_update(payload)

    db.add(u)
    await db.commit()
    await db.refresh(u)
    await log_event(
        db,
        "user.updated",
        actor=current_admin,
        target=f"user:{u.username}",
        request=request,
    )
    return u


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    request: Request,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a user, preventing self-deletion and removal of the last admin."""
    if user_id == current_admin.id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account"
        )
    u = (
        await db.exec(
            select(User).where(User.id == user_id).options(selectinload(User.roles))  # type: ignore[arg-type]
        )
    ).one_or_none()
    if not u:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    await ensure_not_last_active_admin(db, u)
    username = u.username
    await db.delete(u)
    await db.commit()
    await log_event(
        db,
        "user.deleted",
        actor=current_admin,
        target=f"user:{username}",
        request=request,
    )
