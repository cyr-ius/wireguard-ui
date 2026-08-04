"""Authentication router: login, current user, password change."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession

from ..auth import (
    clear_auth_cookies,
    create_access_token,
    get_current_user,
    get_current_user_optional,
    hash_password,
    set_auth_cookies,
    verify_password,
)
from ..config import app_settings
from ..database import get_db
from ..models import User
from ..schemas import (
    AppConfigResponse,
    LoginRequest,
    PasswordChangeRequest,
    TokenResponse,
    UserResponse,
)
from ..services.audit import log_event
from ..services.auth import authenticate_user, local_login_allowed

router = APIRouter()


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    request: Request,
    response: Response,
    credentials: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """OAuth2 password-flow token endpoint used by the Swagger UI."""
    if not await local_login_allowed(db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Local authentication is disabled. Use OIDC sign-in instead.",
        )
    try:
        user = await authenticate_user(db, credentials.username, credentials.password)
    except HTTPException:
        await log_event(
            db,
            "auth.login_failed",
            actor=credentials.username,
            request=request,
            success=False,
        )
        raise
    token = create_access_token({"sub": user.username})
    set_auth_cookies(response, request, token)
    await log_event(db, "auth.login", actor=user, request=request)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate and return a JWT access token, setting the session cookie."""
    if not await local_login_allowed(db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Local authentication is disabled. Use OIDC sign-in instead.",
        )
    try:
        user = await authenticate_user(db, credentials.username, credentials.password)
    except HTTPException:
        await log_event(
            db,
            "auth.login_failed",
            actor=credentials.username,
            request=request,
            success=False,
        )
        raise
    token = create_access_token({"sub": user.username})
    set_auth_cookies(response, request, token)
    await log_event(db, "auth.login", actor=user, request=request)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Clear the session and CSRF cookies, regardless of whether they were still valid."""
    clear_auth_cookies(response, request)
    user = await get_current_user_optional(request, db)
    if user is not None:
        await log_event(db, "auth.logout", actor=user, request=request)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return UserResponse.model_validate(current_user)


@router.get("/config", response_model=AppConfigResponse)
async def get_app_config(_: User = Depends(get_current_user)):
    """Return client-facing feature flags (e.g. whether PATs are enabled)."""
    return AppConfigResponse(api_keys_enabled=app_settings.api_keys_enabled)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: PasswordChangeRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the current user's password after verifying the old one."""
    if current_user.auth_source != "local":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password change is not available for externally managed accounts",
        )
    if not verify_password(body.current_password, str(current_user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    current_user.sqlmodel_update({"hashed_password": hash_password(body.new_password)})
    db.add(current_user)
    await db.commit()
    await log_event(db, "auth.password_changed", actor=current_user, request=request)
