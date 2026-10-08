from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import auth
from ..config import Settings, get_settings
from ..db import get_session
from ..models import RefreshToken, User
from ..schemas import AccessTokenResponse, LoginRequest, RegisterRequest, UserResponse

router = APIRouter(prefix="/v1/auth", tags=["auth"])
# impl plan §1.4: GET /v1/me is top-level, unlike every other auth endpoint (/v1/auth/*).
# Second router in this module (not a separate file) since it shares get_current_user below.
me_router = APIRouter(prefix="/v1", tags=["auth"])

REFRESH_COOKIE_NAME = "shorts_maker_refresh"


def _set_refresh_cookie(response: Response, raw_token: str, settings: Settings) -> None:
    # impl plan §1.3: "strict cookie attributes" -- HttpOnly + Secure + SameSite=strict, never
    # readable from JS (CSRF/XSS defense in depth alongside the double-submit-free design of
    # keeping the access token out of cookies entirely).
    response.set_cookie(
        REFRESH_COOKIE_NAME, raw_token, max_age=settings.refresh_token_ttl_seconds,
        httponly=True, secure=settings.deployment_mode != "D0", samesite="strict", path="/v1/auth",
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, session: AsyncSession = Depends(get_session)):
    existing = (await session.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "email already registered")
    user = User(email=body.email, password_hash=auth.hash_password(body.password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return UserResponse(id=user.id, email=user.email, created_at=user.created_at)


@router.post("/login", response_model=AccessTokenResponse)
async def login(body: LoginRequest, response: Response, settings: Settings = Depends(get_settings),
                 session: AsyncSession = Depends(get_session)):
    user = (await session.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if user is None or not auth.verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")

    raw_refresh = auth.generate_refresh_token()
    session.add(RefreshToken(
        user_id=user.id, token_hash=auth.hash_refresh_token(raw_refresh),
        expires_at=datetime.now(UTC) + timedelta(seconds=settings.refresh_token_ttl_seconds),
    ))
    await session.commit()
    _set_refresh_cookie(response, raw_refresh, settings)

    access = auth.issue_access_token(subject=str(user.id), secret_key=settings.auth_secret_key,
                                      ttl_seconds=settings.access_token_ttl_seconds)
    return AccessTokenResponse(access_token=access, expires_in=settings.access_token_ttl_seconds)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(response: Response, settings: Settings = Depends(get_settings),
                   session: AsyncSession = Depends(get_session),
                   shorts_maker_refresh: str | None = Cookie(default=None)):
    if shorts_maker_refresh is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "no refresh token")
    token_hash = auth.hash_refresh_token(shorts_maker_refresh)
    row = (await session.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))).scalar_one_or_none()
    now = datetime.now(UTC)
    if row is None or row.revoked_at is not None or row.expires_at <= now:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or expired refresh token")

    # Rotation: revoke the presented token, issue a brand new one (impl plan §1.3 "rotating
    # refresh tokens"). A reused/revoked token can never mint a fresh session.
    new_raw = auth.generate_refresh_token()
    new_row = RefreshToken(
        user_id=row.user_id, token_hash=auth.hash_refresh_token(new_raw),
        expires_at=now + timedelta(seconds=settings.refresh_token_ttl_seconds),
    )
    session.add(new_row)
    await session.flush()
    row.revoked_at = now
    row.replaced_by_id = new_row.id
    await session.commit()
    _set_refresh_cookie(response, new_raw, settings)

    access = auth.issue_access_token(subject=str(row.user_id), secret_key=settings.auth_secret_key,
                                      ttl_seconds=settings.access_token_ttl_seconds)
    return AccessTokenResponse(access_token=access, expires_in=settings.access_token_ttl_seconds)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response, session: AsyncSession = Depends(get_session),
                  shorts_maker_refresh: str | None = Cookie(default=None)):
    if shorts_maker_refresh is not None:
        token_hash = auth.hash_refresh_token(shorts_maker_refresh)
        row = (await session.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))).scalar_one_or_none()
        if row is not None and row.revoked_at is None:
            row.revoked_at = datetime.now(UTC)
            await session.commit()
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/v1/auth")


async def get_current_user(
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_session),
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    """Dependency used by every non-auth router. FastAPI extracts the Authorization header
    itself via the Header() annotation -- no manual request-object parsing needed."""
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    token = authorization.removeprefix("Bearer ")
    try:
        payload = auth.verify_access_token(token, secret_key=settings.auth_secret_key)
    except auth.InvalidAccessToken as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e)) from e
    user = await session.get(User, uuid.UUID(payload.subject))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not found")
    return user


@me_router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return UserResponse(id=user.id, email=user.email, created_at=user.created_at)