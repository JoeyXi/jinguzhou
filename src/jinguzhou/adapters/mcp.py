"""MCP tool-call adapter helpers."""

from __future__ import annotations

from typing import Any, Optional

from jinguzhou.tools.adapters import NormalizedToolCall, ToolAdapterRegistry


class MCPToolAdapter:
    """Normalize MCP tool call payloads through the Jinguzhou adapter registry."""

    def __init__(self, registry: Optional[ToolAdapterRegistry] = None) -> None:
        self.registry = registry or ToolAdapterRegistry.with_defaults()

    def normalize_call(
        self,
        name: str,
        arguments: Any,
        *,
        call_id: str = "",
        raw_payload: Any = None,
    ) -> NormalizedToolCall:
        """Normalize one MCP tool call name and argument payload."""
        return self.registry.normalize_tool_call(
            protocol="mcp",
            tool_name=name,
            arguments=arguments,
            id=call_id,
            type="tools/call",
            raw_payload=raw_payload,
            metadata={"framework": "mcp"},
        )

    def extract_calls(self, payload: dict[str, Any]) -> list[NormalizedToolCall]:
        """Extract MCP tool calls from JSON-RPC or content-block payloads."""
        return [
            call
            for call in self.registry.extract_tool_calls(payload)
            if call.protocol == "mcp"
        ]

    def normalize_jsonrpc_request(self, payload: dict[str, Any]) -> NormalizedToolCall:
        """Normalize a single MCP JSON-RPC `tools/call` request."""
        calls = self.extract_calls(payload)
        if not calls:
            raise ValueError("Payload does not contain an MCP tools/call request.")
        if len(calls) > 1:
            raise ValueError("Expected one MCP tool call, found multiple calls.")
        return calls[0]


def build_mcp_tool_call_request(
    name: str,
    arguments: Any,
    *,
    call_id: str = "jinguzhou-mcp-call",
    jsonrpc: str = "2.0",
) -> dict[str, Any]:
    """Build a small MCP JSON-RPC tool-call request for examples and tests."""
    return {
        "jsonrpc": jsonrpc,
        "id": call_id,
        "method": "tools/call",
        "params": {
            "name": name,
            "arguments": arguments,
        },
    }


def normalize_mcp_tool_call(
    name: str,
    arguments: Any,
    *,
    call_id: str = "",
    registry: Optional[ToolAdapterRegistry] = None,
) -> NormalizedToolCall:
    """Normalize one MCP tool call without constructing an adapter explicitly."""
    return MCPToolAdapter(registry).normalize_call(name, arguments, call_id=call_id)
