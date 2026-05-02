"""OpenAI Agents SDK tool-call adapter helpers."""

from __future__ import annotations

from typing import Any, Optional

from jinguzhou.tools.adapters import NormalizedToolCall, ToolAdapterRegistry


class OpenAIAgentsToolAdapter:
    """Normalize OpenAI Agents-style function calls through the shared registry."""

    def __init__(self, registry: Optional[ToolAdapterRegistry] = None) -> None:
        self.registry = registry or ToolAdapterRegistry.with_defaults()

    def normalize_function_call(
        self,
        name: str,
        arguments: Any,
        *,
        call_id: str = "",
        raw_payload: Any = None,
    ) -> NormalizedToolCall:
        """Normalize one OpenAI Agents SDK function call."""
        return self.registry.normalize_tool_call(
            protocol="openai_agents",
            tool_name=name,
            arguments=arguments,
            id=call_id,
            type="function_call",
            raw_payload=raw_payload,
            metadata={"framework": "openai_agents"},
        )

    def extract_calls(self, payload: dict[str, Any]) -> list[NormalizedToolCall]:
        """Extract tool calls from an OpenAI Agents-style response payload."""
        return [
            call
            for call in self.registry.extract_tool_calls(payload)
            if call.protocol == "openai_agents"
        ]

    def normalize_response_item(self, payload: dict[str, Any]) -> NormalizedToolCall:
        """Normalize a single OpenAI Agents function-call output item."""
        calls = self.extract_calls({"output": [payload]})
        if not calls:
            raise ValueError("Payload does not contain an OpenAI Agents function call.")
        return calls[0]


def build_openai_agents_function_call(
    name: str,
    arguments: Any,
    *,
    call_id: str = "jinguzhou-openai-agents-call",
) -> dict[str, Any]:
    """Build a small OpenAI Agents-style function-call item for examples and tests."""
    return {
        "type": "function_call",
        "call_id": call_id,
        "name": name,
        "arguments": arguments,
    }


def normalize_openai_agents_function_call(
    name: str,
    arguments: Any,
    *,
    call_id: str = "",
    registry: Optional[ToolAdapterRegistry] = None,
) -> NormalizedToolCall:
    """Normalize one OpenAI Agents function call without constructing an adapter."""
    return OpenAIAgentsToolAdapter(registry).normalize_function_call(
        name,
        arguments,
        call_id=call_id,
    )
