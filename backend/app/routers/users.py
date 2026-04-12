"""User management router — admin only."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..auth import get_current_admin, hash_password
from ..database import get_db
from ..models import Role, User
from ..schemas import RoleResponse, UserCreate, UserResponse, UserUpdate

router = APIRouter()


async def _load_roles(db: AsyncSession, role_ids: list[int]) -> list[Role]:
    if not role_ids:
        raise HTTPException(status_code=400, detail="Role is required")

    result = await db.exec(select(Role).where(Role.id.in_(role_ids)))
    roles = result.all()
    role_by_id = {r.id: r for r in roles if r.id is not None}

    # Keep the input order and silently ignore unknown role ids (current behavior).
    return [role_by_id[rid] for rid in role_ids if rid in role_by_id]


@router.get("", response_model=list[UserResponse])
async def list_users(
    _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
):
    result = await db.exec(
        select(User).options(selectinload(User.roles)).order_by(User.username)  # type: ignore
    )
    return result.all()


@router.get("/utils/roles", response_model=list[RoleResponse])
async def list_roles(
    _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
):
    result = await db.exec(select(Role).order_by(Role.name))
    return result.all()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    for field, value, msg in [
        (User.username, data.username, "Username already in use"),
        (User.email, data.email, "Email already in use"),
    ]:
        if (await db.exec(select(User).where(field == value))).one_or_none():
            raise HTTPException(422, detail=msg)

    payload = data.model_dump(exclude={"password", "role_ids"})
    payload["hashed_password"] = hash_password(data.password)
    user = User.model_validate(payload)
    user.roles = await _load_roles(db, data.role_ids)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    result = await db.exec(
        select(User).where(User.id == user.id).options(selectinload(User.roles))  # type: ignore
    )
    return result.one()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    u = (
        await db.exec(
            select(User).where(User.id == user_id).options(selectinload(User.roles))  # type: ignore
        )
    ).one_or_none()
    if not u:
        raise HTTPException(404, detail="User not found")
    return u


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    u = (
        await db.exec(
            select(User).where(User.id == user_id).options(selectinload(User.roles))  # type: ignore
        )
    ).one_or_none()
    if not u:
        raise HTTPException(404, detail="User not found")

    payload = data.model_dump(exclude_unset=True)
    if "email" in payload and payload["email"] != u.email:
        existing_user = (
            await db.exec(select(User).where(User.email == payload["email"]))
        ).one_or_none()
        if existing_user:
            raise HTTPException(422, detail="Email already in use")

    if "role_ids" in payload:
        u.roles = await _load_roles(db, payload.pop("role_ids"))
    u.sqlmodel_update(payload)

    db.add(u)
    await db.commit()
    result = await db.exec(
        select(User).where(User.id == user_id).options(selectinload(User.roles))  # type: ignore
    )
    return result.one()


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    if user_id == current_admin.id:
        raise HTTPException(400, detail="Cannot delete your own account")
    u = await db.get(User, user_id)
    if not u:
        raise HTTPException(404, detail="User not found")
    await db.delete(u)
    await db.commit()
