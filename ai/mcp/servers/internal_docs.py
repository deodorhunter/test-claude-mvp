"""
Internal documentation MCP server stub.

Returns fixed demo data with high confidence (0.95).
"""

from ai.mcp.base import MCPServer, MCPResult


class InternalDocsServer(MCPServer):
    """Stub MCP server for internal documentation queries."""

    name = "internal_docs"
    trust_score = 0.95  # High trust for internal documentation

    async def query(self, input_text: str) -> MCPResult:
        """
        Query internal documentation (stub implementation).

        Returns a fixed demo result with high confidence.

        Args:
            input_text: The query input (ignored in stub).

        Returns:
            MCPResult with demo documentation data.
        """
        # Stub implementation: return fixed demo data
        demo_data = (
            "Internal Documentation: This is a demo response from the internal_docs MCP server. "
            "In production, this would query an actual documentation index or knowledge base. "
            "Query input received: " + input_text[:50]
        )

        return MCPResult(
            data=demo_data,
            source="internal_docs",
            confidence=self.trust_score,
        )
