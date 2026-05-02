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
from jinguzhou.adapters.llamaindex import (
    LlamaIndexToolAdapter,
    build_llamaindex_tool_call,
    normalize_llamaindex_tool_call,
)
from jinguzhou.adapters.openai_agents import (
    OpenAIAgentsToolAdapter,
    build_openai_agents_function_call,
    normalize_openai_agents_function_call,
)

__all__ = [
    "LlamaIndexToolAdapter",
    "MCPToolAdapter",
    "NormalizedToolCall",
    "OpenAIAgentsToolAdapter",
    "ToolAdapterConfig",
    "ToolAdapterRegistry",
    "ToolInvocation",
    "build_llamaindex_tool_call",
    "build_mcp_tool_call_request",
    "build_openai_agents_function_call",
    "normalize_llamaindex_tool_call",
    "normalize_mcp_tool_call",
    "normalize_openai_agents_function_call",
]
