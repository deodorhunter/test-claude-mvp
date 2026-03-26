from datetime import datetime, timedelta, timezone
from typing import Any
from jose import JWTError, jwt
from ..config import get_settings

ALGORITHM = "HS256"


def create_access_token(data: dict[str, Any]) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iss": "ai-platform", "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iss": "ai-platform", "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str, token_type: str = "access") -> dict[str, Any]:
    """Verify a JWT and return its payload. Raises JWTError on any failure."""
    settings = get_settings()
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("iss") != "ai-platform":
        raise JWTError("Invalid issuer")
    if payload.get("type") != token_type:
        raise JWTError(f"Expected token type '{token_type}', got '{payload.get('type')}'")
    return payload
