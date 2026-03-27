import base64
import json
import logging
from dataclasses import dataclass

import httpx

from ..config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class PloneIdentity:
    username: str
    roles: list[str]
    tenant_id: str


def _extract_username_from_jwt(token: str) -> str:
    """
    Decode the JWT payload (without signature verification) to extract the
    username from the 'sub' claim. Signature verification was already done by
    Plone when it issued the token; we just need the subject identifier here.
    """
    try:
        # JWT format: header.payload.signature — all base64url-encoded
        payload_b64 = token.split(".")[1]
        # Add padding if needed
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        username = payload.get("sub")
        if not username:
            raise ValueError("No 'sub' claim in Plone JWT payload")
        return username
    except (IndexError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"Cannot extract username from Plone token: {exc}"
        ) from exc


class PloneIdentityAdapter:
    """Verifies a Plone auth token and returns the user's identity and roles."""

    async def get_identity(
        self, plone_token: str, tenant_id: str
    ) -> PloneIdentity:
        """
        Verifies the Plone token by calling @users/{username} and returns the
        user's identity and roles.

        Strategy:
        1. Decode the JWT payload to get the username ('sub' claim) — no
           signature verification needed here because Plone signed it and we
           will confirm it's valid by using it to call Plone's REST API.
        2. Call GET @users/{username} with the Bearer token — if Plone rejects
           the token (401/403) or the user doesn't exist (404), we propagate
           the error.

        Raises:
            httpx.HTTPStatusError: 401/403 if token invalid, 404 if user not found
            httpx.ConnectError: if Plone is unreachable
            ValueError: if the token payload cannot be decoded
        """
        username = _extract_username_from_jwt(plone_token)

        settings = get_settings()
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.PLONE_BASE_URL}/@users/{username}",
                headers={
                    "Authorization": f"Bearer {plone_token}",
                    "Accept": "application/json",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        resolved_username = data.get("username") or data.get("id") or username
        roles: list[str] = data.get("roles", [])

        return PloneIdentity(
            username=resolved_username, roles=roles, tenant_id=tenant_id
        )
