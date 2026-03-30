import asyncio
import logging
from ai.mcp.registry import MCPRegistry
from ai.context.sanitizer import sanitize

logger = logging.getLogger(__name__)
_SERVER_TIMEOUT = 3.0


class ContextBuilder:
    def __init__(self, registry: MCPRegistry, audit_service=None):
        self._registry = registry
        self._audit_service = audit_service

    async def build(self, query: str, tenant_id: str | None = None) -> str:
        """
        Build assembled context by querying all registered MCP servers in parallel.

        Args:
            query: The context query string
            tenant_id: Optional tenant ID for audit logging

        Returns:
            Formatted context string with source attribution and confidence scores.
            Each chunk is prefixed with [Fonte: {source} | confidence: {confidence:.2f}]
            Chunks are separated by double newlines.
            Output is sanitized against prompt injection patterns.
        """
        servers = self._registry.get_all_servers()

        async def _query_one(server):
            """Query a single MCP server with timeout."""
            try:
                return await asyncio.wait_for(server.query(query), timeout=_SERVER_TIMEOUT)
            except asyncio.TimeoutError:
                logger.warning("MCP server %s timed out after %ss", server.name, _SERVER_TIMEOUT)
                return None
            except Exception as exc:
                logger.error("MCP server %s error: %s", server.name, exc)
                return None

        # Query all servers in parallel
        raw_results = await asyncio.gather(*[_query_one(s) for s in servers])

        chunks = []
        for result in raw_results:
            # Skip None results (timeouts/errors)
            if result is None:
                continue
            # Skip results below confidence threshold
            if result.confidence < self._registry.min_confidence:
                continue

            # Log successful retrieval to audit service if available
            if self._audit_service:
                await self._audit_service.log(
                    action="mcp_query",
                    resource=result.source,
                    tenant_id=tenant_id,
                    metadata={"confidence": result.confidence},
                )

            # Sanitize the data to prevent prompt injection
            safe_data = sanitize(result.data)

            # Format chunk with source attribution and confidence
            chunk = f"[Fonte: {result.source} | confidence: {result.confidence:.2f}]\n{safe_data}"
            chunks.append(chunk)

        return "\n\n".join(chunks)
