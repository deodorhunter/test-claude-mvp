"""
MCP Registry for managing and querying MCP servers with trust-based filtering.

The registry maintains a collection of MCP servers, filters results by trust score,
and logs all MCP queries to the audit service.
"""

import logging
from typing import Optional

from ai.mcp.base import MCPServer, MCPResult

logger = logging.getLogger(__name__)


class MCPRegistry:
    """
    Registry of available MCP servers with trust-based filtering.

    Maintains a map of MCP servers, executes queries against all servers,
    filters results below min_confidence threshold, and logs audit entries.
    """

    def __init__(self, min_confidence: float = 0.5):
        """
        Initialize the MCP registry.

        Args:
            min_confidence: Minimum confidence threshold for including results.
                Results with confidence < min_confidence are filtered out.
                Defaults to 0.5.
        """
        self._servers: dict[str, MCPServer] = {}
        self.min_confidence = min_confidence

    def register(self, server: MCPServer) -> None:
        """
        Register an MCP server in the registry.

        Args:
            server: The MCPServer instance to register.
        """
        if not hasattr(server, 'name') or not server.name:
            raise ValueError("MCPServer must have a 'name' attribute")
        self._servers[server.name] = server
        logger.debug(f"Registered MCP server: {server.name}")

    def get(self, name: str) -> Optional[MCPServer]:
        """
        Retrieve a registered MCP server by name.

        Args:
            name: The name of the server to retrieve.

        Returns:
            The MCPServer instance, or None if not found.
        """
        return self._servers.get(name)

    def get_all_servers(self) -> list[MCPServer]:
        """Return all registered servers."""
        return list(self._servers.values())

    async def query_all(
        self,
        input_text: str,
        audit_service=None,
        tenant_id=None,
    ) -> list[MCPResult]:
        """
        Query all registered MCP servers and filter results by trust score.

        Results below min_confidence are filtered out. Each server is queried
        and an audit log entry is created for every query attempt (before filtering).

        Args:
            input_text: The query input to pass to all servers.
            audit_service: Optional audit service for logging queries.
            tenant_id: Optional tenant_id for audit log context.

        Returns:
            List of MCPResult objects with confidence >= min_confidence.
        """
        results = []

        for server_name, server in self._servers.items():
            try:
                # Query the server
                result = await server.query(input_text)

                # Log the query attempt to audit service if provided
                if audit_service:
                    await audit_service.log(
                        action="mcp_query",
                        resource=server_name,
                        tenant_id=tenant_id,
                        metadata={
                            "confidence": result.confidence,
                            "min_confidence": self.min_confidence,
                            "filtered": result.confidence < self.min_confidence,
                        },
                    )

                # Filter by confidence threshold
                if result.confidence >= self.min_confidence:
                    results.append(result)
                    logger.debug(
                        f"MCP query {server_name} passed filter "
                        f"(confidence={result.confidence:.2f})"
                    )
                else:
                    logger.debug(
                        f"MCP query {server_name} filtered out "
                        f"(confidence={result.confidence:.2f} < {self.min_confidence})"
                    )

            except Exception as exc:
                # Log the error but continue with other servers
                logger.error(
                    f"MCP query to {server_name} failed: {exc}",
                    exc_info=True,
                )
                if audit_service:
                    await audit_service.log(
                        action="mcp_query",
                        resource=server_name,
                        tenant_id=tenant_id,
                        metadata={
                            "error": str(exc),
                        },
                    )

        return results
