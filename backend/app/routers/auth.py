"""Authentication router: login, current user, password change."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..auth import create_access_token, get_current_user, hash_password, verify_password
from ..database import get_db
from ..models import GlobalSettings, User
from ..schemas import LoginRequest, PasswordChangeRequest, TokenResponse, UserResponse

router = APIRouter()


async def _local_login_allowed(db: AsyncSession) -> bool:
    settings = (await db.exec(select(GlobalSettings))).one_or_none()
    if settings is None:
        return True
    return not (settings.oidc_enabled and settings.oidc_only)


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    credentials: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """OAuth2 password-flow token endpoint used by the Swagger UI."""
    if not await _local_login_allowed(db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Local authentication is disabled. Use OIDC sign-in instead.",
        )

    result = await db.exec(
        select(User)
        .where(User.username == credentials.username)
        .options(selectinload(User.roles))  # type: ignore
    )
    user = result.one_or_none()

    if not user or not verify_password(credentials.password, str(user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled"
        )

    token = create_access_token({"sub": user.username})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate and return a JWT access token."""
    if not await _local_login_allowed(db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Local authentication is disabled. Use OIDC sign-in instead.",
        )

    result = await db.exec(
        select(User)
        .where(User.username == credentials.username)
        .options(selectinload(User.roles))  # type: ignore
    )
    user = result.one_or_none()

    if not user or not verify_password(credentials.password, str(user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    if user.active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled"
        )

    token = create_access_token({"sub": user.username})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return UserResponse.model_validate(current_user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the current user's password after verifying the old one."""
    if not verify_password(body.current_password, str(current_user.hashed_password)):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.sqlmodel_update({"hashed_password": hash_password(body.new_password)})
    db.add(current_user)
    await db.commit()
