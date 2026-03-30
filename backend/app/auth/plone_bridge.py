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


class PloneIdentityAdapter:
    """Verifies a Plone auth token and returns the user's identity and roles."""

    async def get_identity(
        self, plone_token: str, tenant_id: str
    ) -> PloneIdentity:
        """
        Verifies the Plone token by calling @users/@current and returns the
        user's identity and roles.

        Raises:
            httpx.HTTPStatusError: 401/403 if token invalid, 404 if user not found
            httpx.ConnectError: if Plone is unreachable
        """
        settings = get_settings()
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.PLONE_BASE_URL}/@users/@current",
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
