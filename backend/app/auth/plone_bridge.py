"""
Plone JWT Authentication Bridge

This module handles JWT token validation for Plone CMS integration.
It does NOT implement MCP (Model Context Protocol) functionality — that is handled separately
by the plone-mcp Node.js server in infra/plone-mcp/ and its Python adapter in ai/mcp/servers/plone.py.

Purpose:
  - Validate Plone-issued Bearer tokens via the Plone REST API /@users/@current endpoint
  - Extract user identity (username, roles) and tenant context from Plone
  - Return structured PloneIdentity for use in the AI Platform auth layer

Do not confuse this module with:
  - infra/plone-mcp/ — MCP server for content operations (CRUD, search, workflow on Plone)
  - ai/mcp/servers/plone.py — Python adapter wrapping plone-mcp for the MCPRegistry

See docs/ARCHITECTURE_STATE.md "Plone Integration Points" for a diagram.
"""

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
