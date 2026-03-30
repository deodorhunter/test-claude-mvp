"""
MCP Server base class and protocol.

All MCP servers implement the MCPServer interface with an async query() method
that returns MCPResult containing data, source, and confidence score.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class MCPResult:
    """Result returned by an MCP server query."""
    data: str
    source: str
    confidence: float  # 0.0 to 1.0


class MCPServer(ABC):
    """
    Abstract base class for MCP (Model Context Protocol) servers.

    Subclasses must implement async query() and set trust_score as a class attribute.
    """

    name: str  # Subclass must set this
    trust_score: float = 0.5  # Default trust score; subclasses should override

    @abstractmethod
    async def query(self, input_text: str) -> MCPResult:
        """
        Query this MCP server and return a result with data, source, and confidence.

        Args:
            input_text: The query input.

        Returns:
            MCPResult with data, source, and confidence.
        """
        ...
