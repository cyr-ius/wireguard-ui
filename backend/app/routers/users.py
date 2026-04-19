"""User management router — admin only."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..auth import get_current_admin, hash_password
from ..database import get_db
from ..models import Role, User
from ..schemas import RoleResponse, UserCreate, UserResponse, UserUpdate
from ..services.users import load_roles

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
    _: User = Depends(get_current_admin),
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
    return result.one()


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
    _: User = Depends(get_current_admin),
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
    if "email" in payload and payload["email"] != u.email:
        if (
            await db.exec(select(User).where(User.email == payload["email"]))
        ).one_or_none():
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Email already in use"
            )

    if "role_ids" in payload:
        u.roles = await load_roles(db, payload.pop("role_ids"))
    u.sqlmodel_update(payload)

    db.add(u)
    await db.commit()
    result = await db.exec(
        select(User).where(User.id == user_id).options(selectinload(User.roles))  # type: ignore[arg-type]
    )
    return result.one()


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a user, preventing self-deletion."""
    if user_id == current_admin.id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account"
        )
    u = await db.get(User, user_id)
    if not u:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    await db.delete(u)
    await db.commit()
