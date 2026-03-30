"""
Model Context Protocol (MCP) integration — registry, servers, and trust scoring.

This module provides:
- MCPServer: abstract base class for all MCP servers
- MCPRegistry: registry with trust-based filtering and audit logging
- InternalDocsServer, WebServer: stub implementations
"""

from ai.mcp.base import MCPServer, MCPResult
from ai.mcp.registry import MCPRegistry
from ai.mcp.servers import InternalDocsServer, WebServer

__all__ = [
    "MCPServer",
    "MCPResult",
    "MCPRegistry",
    "InternalDocsServer",
    "WebServer",
]
