"""
Plone MCP Server adapter — queries Plone CMS content via REST API.

Uses the Plone REST API /@search endpoint directly (no proxy through the
self-hosted plone-mcp Node.js service, which is exposed for external MCP clients
such as Claude Desktop).

Auth: HTTP Basic via PLONE_USERNAME / PLONE_PASSWORD env vars.
Output is always passed through the sanitizer before returning.
"""

import logging
import os
from typing import Optional

import httpx

from ai.mcp.base import MCPResult, MCPServer
from ai.context.sanitizer import sanitize

logger = logging.getLogger(__name__)

# Trust score for first-party CMS content — above default min_confidence of 0.5
_TRUST_SCORE = 0.85
# Timeout for Plone REST API calls (seconds)
_REQUEST_TIMEOUT = 10.0


class PloneMCPServer(MCPServer):
    """
    MCP server that retrieves content from the self-hosted Plone CMS.

    Calls Plone REST API /@search with the input text as a full-text query.
    Returns a formatted MCPResult with titles, descriptions, and source URLs.
    """

    name = "plone"
    trust_score = _TRUST_SCORE

    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        self._base_url = (base_url or os.environ.get("PLONE_BASE_URL", "")).rstrip("/")
        self._username = username or os.environ.get("PLONE_USERNAME", "")
        self._password = password or os.environ.get("PLONE_PASSWORD", "")

    async def query(self, input_text: str) -> MCPResult:
        """
        Search Plone content matching input_text.

        Returns MCPResult with sanitized data, first-result URL as source,
        and trust_score as confidence. Raises on network/auth errors so that
        MCPRegistry can log and continue.
        """
        search_url = f"{self._base_url}/@search"
        params = {"SearchableText": input_text, "b_size": 5}

        async with httpx.AsyncClient(
            auth=(self._username, self._password),
            timeout=_REQUEST_TIMEOUT,
            headers={"Accept": "application/json"},
        ) as client:
            response = await client.get(search_url, params=params)

        response.raise_for_status()
        payload = response.json()

        items = payload.get("items", [])
        if not items:
            return MCPResult(
                data=sanitize(f"Nessun contenuto trovato in Plone per: {input_text}"),
                source=self._base_url,
                confidence=self.trust_score,
            )

        lines = []
        for item in items:
            title = item.get("title", "(senza titolo)")
            description = item.get("description", "")
            url = item.get("@id", self._base_url)
            lines.append(f"- {title}: {description} [{url}]")

        raw_data = "\n".join(lines)
        first_url = items[0].get("@id", self._base_url)

        return MCPResult(
            data=sanitize(raw_data),
            source=first_url,
            confidence=self.trust_score,
        )
