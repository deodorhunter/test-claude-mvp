"""
Web search MCP server stub.

Returns fixed demo data with lower confidence (0.4).
"""

from ai.mcp.base import MCPServer, MCPResult


class WebServer(MCPServer):
    """Stub MCP server for web search queries."""

    name = "web"
    trust_score = 0.4  # Lower trust for web search results

    async def query(self, input_text: str) -> MCPResult:
        """
        Query web sources (stub implementation).

        Returns a fixed demo result with lower confidence.

        Args:
            input_text: The query input (ignored in stub).

        Returns:
            MCPResult with demo web search data.
        """
        # Stub implementation: return fixed demo data
        demo_data = (
            "Web Search Result: This is a demo response from the web MCP server. "
            "In production, this would search web sources like documentation sites, blogs, etc. "
            "Note: Web results have lower confidence than internal sources. "
            "Query input received: " + input_text[:50]
        )

        return MCPResult(
            data=demo_data,
            source="web",
            confidence=self.trust_score,
        )
