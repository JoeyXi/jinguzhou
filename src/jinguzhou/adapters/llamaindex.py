"""LlamaIndex tool-call adapter helpers."""

from __future__ import annotations

from typing import Any, Optional

from jinguzhou.tools.adapters import NormalizedToolCall, ToolAdapterRegistry


class LlamaIndexToolAdapter:
    """Normalize LlamaIndex-style tool calls through the shared registry."""

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
        """Normalize one LlamaIndex tool call."""
        return self.registry.normalize_tool_call(
            protocol="llamaindex",
            tool_name=name,
            arguments=arguments,
            id=call_id,
            type="tool_call",
            raw_payload=raw_payload,
            metadata={"framework": "llamaindex"},
        )

    def extract_calls(self, payload: dict[str, Any]) -> list[NormalizedToolCall]:
        """Extract LlamaIndex-style top-level tool calls."""
        return [
            call
            for call in self.registry.extract_tool_calls(payload)
            if call.protocol == "llamaindex"
        ]

    def normalize_tool_selection(self, payload: dict[str, Any]) -> NormalizedToolCall:
        """Normalize a single LlamaIndex-style tool selection payload."""
        calls = self.extract_calls(payload)
        if not calls:
            raise ValueError("Payload does not contain a LlamaIndex tool call.")
        if len(calls) > 1:
            raise ValueError("Expected one LlamaIndex tool call, found multiple calls.")
        return calls[0]


def build_llamaindex_tool_call(
    name: str,
    arguments: Any,
    *,
    call_id: str = "jinguzhou-llamaindex-call",
) -> dict[str, Any]:
    """Build a small LlamaIndex-style tool call payload for examples and tests."""
    return {
        "framework": "llamaindex",
        "tool_calls": [
            {
                "id": call_id,
                "tool_name": name,
                "kwargs": arguments,
            }
        ],
    }


def normalize_llamaindex_tool_call(
    name: str,
    arguments: Any,
    *,
    call_id: str = "",
    registry: Optional[ToolAdapterRegistry] = None,
) -> NormalizedToolCall:
    """Normalize one LlamaIndex tool call without constructing an adapter explicitly."""
    return LlamaIndexToolAdapter(registry).normalize_call(name, arguments, call_id=call_id)
