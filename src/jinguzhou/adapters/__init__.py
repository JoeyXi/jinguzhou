"""Public adapter foundation API."""

from jinguzhou.tools.adapters import (
    NormalizedToolCall,
    ToolAdapterConfig,
    ToolAdapterRegistry,
    ToolInvocation,
)
from jinguzhou.adapters.mcp import (
    MCPToolAdapter,
    build_mcp_tool_call_request,
    normalize_mcp_tool_call,
)

__all__ = [
    "MCPToolAdapter",
    "NormalizedToolCall",
    "ToolAdapterConfig",
    "ToolAdapterRegistry",
    "ToolInvocation",
    "build_mcp_tool_call_request",
    "normalize_mcp_tool_call",
]
