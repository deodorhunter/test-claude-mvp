from dataclasses import dataclass
import httpx
from ..config import get_settings


@dataclass
class PloneIdentity:
    username: str
    roles: list[str]
    tenant_id: str


class PloneIdentityAdapter:
    """Verifies a Plone auth token and returns the user's identity and roles."""

    async def get_identity(self, plone_token: str, tenant_id: str) -> PloneIdentity:
        """
        Calls Plone's @users endpoint to verify the token and extract identity.

        Raises:
            httpx.HTTPStatusError: 401 if token invalid, 404 if user not found
            httpx.ConnectError: if Plone is unreachable
        """
        settings = get_settings()
        async with httpx.AsyncClient(timeout=10.0) as client:
            # First, get the currently logged-in user's info using the token
            resp = await client.get(
                f"{settings.PLONE_BASE_URL}/@users/@current",
                headers={"Authorization": f"Bearer {plone_token}", "Accept": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()

        username = data.get("username") or data.get("id") or data.get("login")
        if not username:
            raise ValueError("Could not extract username from Plone @users/@current response")

        # Extract roles — Plone returns roles as list of strings under 'roles'
        roles: list[str] = data.get("roles", [])

        return PloneIdentity(username=username, roles=roles, tenant_id=tenant_id)
