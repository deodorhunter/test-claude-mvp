import uuid
from dataclasses import dataclass
from fastapi import Cookie, HTTPException, status
from jose import JWTError
from .jwt import verify_token


@dataclass
class CurrentUser:
    id: uuid.UUID
    tenant_id: uuid.UUID
    roles: list[str]
    plone_username: str


async def get_current_user(ai_platform_token: str | None = Cookie(default=None)) -> CurrentUser:
    """
    FastAPI dependency. Reads the httpOnly cookie, verifies JWT, returns CurrentUser.
    Raises HTTP 401 on any failure. Never reads tenant_id or user_id from request body.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not ai_platform_token:
        raise credentials_exception
    try:
        payload = verify_token(ai_platform_token, token_type="access")
        user_id_str: str | None = payload.get("sub")
        tenant_id_str: str | None = payload.get("tenant_id")
        plone_username: str | None = payload.get("plone_user")
        roles: list[str] = payload.get("roles", [])
        if not user_id_str or not tenant_id_str:
            raise credentials_exception
        return CurrentUser(
            id=uuid.UUID(user_id_str),
            tenant_id=uuid.UUID(tenant_id_str),
            roles=roles,
            plone_username=plone_username or "",
        )
    except (JWTError, ValueError):
        raise credentials_exception
