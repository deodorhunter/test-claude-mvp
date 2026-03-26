import uuid
import logging
from fastapi import APIRouter, Cookie, HTTPException, Response, status
from pydantic import BaseModel
import httpx
from sqlalchemy import select
from ...auth.jwt import create_access_token, create_refresh_token, verify_token
from ...auth.plone_bridge import PloneIdentityAdapter
from ...db.base import get_db
from ...db.models.user import User
from ...config import get_settings
from ...audit.service import AuditAction, AuditService, get_audit_service
from jose import JWTError
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

_COOKIE_KWARGS = dict(httponly=True, samesite="strict", secure=False)  # secure=True in production


class PloneLoginRequest(BaseModel):
    plone_token: str
    tenant_id: str


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    settings = get_settings()
    secure = settings.ENVIRONMENT == "production"
    response.set_cookie("ai_platform_token", access_token, httponly=True, samesite="strict", secure=secure, max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    response.set_cookie("ai_platform_refresh", refresh_token, httponly=True, samesite="strict", secure=secure, max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400)


@router.post("/plone-login")
async def plone_login(
    body: PloneLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service),
):
    adapter = PloneIdentityAdapter()
    try:
        identity = await adapter.get_identity(body.plone_token, body.tenant_id)
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (401, 403):
            logger.warning("Plone token rejected: %s", e)
            await audit_service.log(AuditAction.LOGIN_FAILURE, resource="plone_login", metadata={"reason": "Invalid Plone token"})
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Plone token")
        if e.response.status_code == 404:
            await audit_service.log(AuditAction.LOGIN_FAILURE, resource="plone_login", metadata={"reason": "Plone user not found"})
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Plone user not found")
        logger.error("Plone returned unexpected error: %s", e)
        await audit_service.log(AuditAction.LOGIN_FAILURE, resource="plone_login", metadata={"reason": "Plone service error"})
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Plone service error")
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.error("Cannot reach Plone: %s", e)
        await audit_service.log(AuditAction.LOGIN_FAILURE, resource="plone_login", metadata={"reason": "Plone service unavailable"})
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Plone service unavailable")

    tenant_id = uuid.UUID(body.tenant_id)

    # Map Plone roles to platform role (highest wins)
    plone_role = _map_plone_role(identity.roles)

    # Upsert user
    result = await db.execute(
        select(User).where(User.plone_username == identity.username, User.tenant_id == tenant_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        user = User(tenant_id=tenant_id, plone_username=identity.username, role=plone_role)
        db.add(user)
    else:
        user.role = plone_role
    await db.commit()
    await db.refresh(user)

    token_data = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "roles": identity.roles,
        "plone_user": identity.username,
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": str(user.id), "tenant_id": str(user.tenant_id)})
    _set_auth_cookies(response, access_token, refresh_token)
    logger.info("Plone login success: user=%s tenant=%s", identity.username, tenant_id)
    await audit_service.log(AuditAction.LOGIN_SUCCESS, resource="plone_login", user_id=user.id, tenant_id=user.tenant_id, metadata={"plone_username": identity.username, "roles": identity.roles})
    return {"detail": "Login successful"}


@router.post("/refresh")
async def refresh_token(
    response: Response,
    ai_platform_refresh: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    if not ai_platform_refresh:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")
    try:
        payload = verify_token(ai_platform_refresh, token_type="refresh")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    user_id = uuid.UUID(payload["sub"])
    tenant_id = uuid.UUID(payload["tenant_id"])

    result = await db.execute(select(User).where(User.id == user_id, User.tenant_id == tenant_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    token_data = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "roles": [user.role],
        "plone_user": user.plone_username,
    }
    access_token = create_access_token(token_data)
    refresh_token_new = create_refresh_token({"sub": str(user.id), "tenant_id": str(user.tenant_id)})
    _set_auth_cookies(response, access_token, refresh_token_new)
    return {"detail": "Token refreshed"}


def _map_plone_role(plone_roles: list[str]) -> str:
    """Map Plone roles to platform role. Highest privilege wins."""
    if "Manager" in plone_roles or "Site Administrator" in plone_roles:
        return "admin"
    if "Editor" in plone_roles or "Reviewer" in plone_roles:
        return "member"
    return "member"  # default for authenticated Plone users
