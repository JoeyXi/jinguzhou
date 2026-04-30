"""Registry for protocol-aware tool call parsing and extractor selection."""

from __future__ import annotations

import json
from fnmatch import fnmatch
from typing import Any, Iterable, Optional

from pydantic import BaseModel, Field

from jinguzhou.policy.models import ToolExtractionConfig


class ToolAdapterConfig(BaseModel):
    """Mapping from tool protocol/name patterns to extraction behavior."""

    name: str
    protocols: list[str] = Field(default_factory=lambda: ["*"])
    tool_name_patterns: list[str] = Field(default_factory=lambda: ["*"])
    canonical_tool_name: str = ""
    extraction: ToolExtractionConfig = Field(default_factory=ToolExtractionConfig)
    priority: int = 0

    def matches(self, protocol: str, tool_name: str) -> bool:
        """Return True when this adapter should handle the tool call."""
        normalized_protocol = protocol or "generic"
        normalized_name = tool_name or ""
        protocol_match = any(
            candidate == "*" or candidate.lower() == normalized_protocol.lower()
            for candidate in self.protocols
        )
        name_match = any(fnmatch(normalized_name, pattern) for pattern in self.tool_name_patterns)
        return protocol_match and name_match


class ToolInvocation(BaseModel):
    """Normalized tool call discovered in a model response."""

    id: str = ""
    protocol: str = "generic"
    type: str = ""
    raw_tool_name: str = ""
    tool_name: str = ""
    tool_payload: Any = Field(default_factory=dict)
    adapter_name: str = "default"
    extraction: ToolExtractionConfig = Field(default_factory=ToolExtractionConfig)
    metadata: dict[str, Any] = Field(default_factory=dict)
    raw_payload: Any = Field(default_factory=dict)

    @property
    def arguments(self) -> Any:
        """Return the normalized tool arguments under the newer adapter name."""
        return self.tool_payload


NormalizedToolCall = ToolInvocation


def _parse_arguments(arguments: Any) -> Any:
    if isinstance(arguments, str):
        try:
            return json.loads(arguments)
        except json.JSONDecodeError:
            return {"raw_arguments": arguments}
    return arguments


def _default_adapter_configs() -> list[ToolAdapterConfig]:
    return [
        ToolAdapterConfig(
            name="filesystem-read",
            protocols=["*"],
            tool_name_patterns=[
                "filesystem.read",
                "filesystem.read_*",
                "filesystem.open",
                "fs.read*",
                "mcp.filesystem.read*",
                "local.fs.read*",
            ],
            canonical_tool_name="filesystem.read",
            extraction=ToolExtractionConfig(
                path_fields=[
                    "path",
                    "paths",
                    "filepath",
                    "file_path",
                    "target_path",
                    "source_path",
                    "destination_path",
                    "directory",
                    "dir",
                    "cwd",
                    "root",
                    "filename",
                    "target",
                    "source",
                    "destination",
                    "location",
                    "$.arguments.path",
                    "$.args.path",
                    "$.input.path",
                    "$.parameters.path",
                    "$.operations[*].target",
                    "$.files[*].path",
                ]
            ),
            priority=95,
        ),
        ToolAdapterConfig(
            name="filesystem-write",
            protocols=["*"],
            tool_name_patterns=[
                "filesystem.write",
                "filesystem.write_*",
                "filesystem.save*",
                "fs.write*",
                "mcp.filesystem.write*",
                "local.fs.write*",
                "custom.fs.write",
            ],
            canonical_tool_name="filesystem.write",
            extraction=ToolExtractionConfig(
                path_fields=[
                    "path",
                    "paths",
                    "filepath",
                    "file_path",
                    "target_path",
                    "source_path",
                    "destination_path",
                    "directory",
                    "dir",
                    "cwd",
                    "root",
                    "filename",
                    "target",
                    "source",
                    "destination",
                    "location",
                    "$.arguments.path",
                    "$.args.path",
                    "$.input.path",
                    "$.parameters.path",
                    "$.operations[*].target",
                    "$.files[*].path",
                ]
            ),
            priority=95,
        ),
        ToolAdapterConfig(
            name="network",
            protocols=["*"],
            tool_name_patterns=[
                "network.*",
                "http.*",
                "fetch",
                "fetch.*",
                "web.request",
                "mcp.fetch.*",
                "custom.fetch",
            ],
            canonical_tool_name="network.request",
            extraction=ToolExtractionConfig(
                url_fields=[
                    "url",
                    "uri",
                    "endpoint",
                    "base_url",
                    "webhook_url",
                    "host",
                    "hostname",
                    "domain",
                    "dest",
                    "destination",
                    "location",
                    "$.request.url",
                    "$.request.destination.url",
                    "$.arguments.url",
                    "$.args.url",
                    "$.input.url",
                ]
            ),
            priority=70,
        ),
        ToolAdapterConfig(
            name="database",
            protocols=["*"],
            tool_name_patterns=[
                "database.*",
                "db.*",
                "sql.*",
                "mcp.database.*",
                "mcp.postgres.*",
                "mcp.sqlite.*",
            ],
            canonical_tool_name="database.query",
            extraction=ToolExtractionConfig(
                db_operation_fields=["operation", "op", "query_type", "method", "action", "kind"],
                sql_fields=[
                    "sql",
                    "query",
                    "statement",
                    "statement_text",
                    "query_text",
                    "$.arguments.sql",
                    "$.args.sql",
                    "$.input.sql",
                    "$.database.statement",
                ],
            ),
            priority=70,
        ),
        ToolAdapterConfig(
            name="shell",
            protocols=["*"],
            tool_name_patterns=[
                "shell",
                "shell.*",
                "terminal.*",
                "bash.*",
                "command.*",
                "mcp.shell.*",
            ],
            canonical_tool_name="shell",
            extraction=ToolExtractionConfig(
                command_fields=[
                    "command",
                    "cmd",
                    "cmdline",
                    "shell_command",
                    "script",
                    "$.arguments.command",
                    "$.args.command",
                    "$.input.command",
                ]
            ),
            priority=70,
        ),
        ToolAdapterConfig(
            name="default",
            protocols=["*"],
            tool_name_patterns=["*"],
            extraction=ToolExtractionConfig(),
            priority=-100,
        ),
    ]


class ToolAdapterRegistry:
    """Registry that parses tool calls and selects extractor configs."""

    def __init__(self, adapters: Optional[Iterable[ToolAdapterConfig]] = None) -> None:
        configured = list(adapters or [])
        self.adapters = sorted(
            configured,
            key=lambda adapter: (adapter.priority, len(adapter.tool_name_patterns)),
            reverse=True,
        )

    @classmethod
    def with_defaults(
        cls,
        custom_adapters: Optional[Iterable[ToolAdapterConfig]] = None,
    ) -> "ToolAdapterRegistry":
        """Build a registry that includes built-in adapters plus custom overrides."""
        combined = list(custom_adapters or []) + _default_adapter_configs()
        return cls(combined)

    def resolve(self, protocol: str, tool_name: str) -> ToolAdapterConfig:
        """Pick the most specific adapter for a tool call."""
        for adapter in self.adapters:
            if adapter.matches(protocol, tool_name):
                return adapter
        return ToolAdapterConfig(name="default")

    def normalize_tool_call(
        self,
        *,
        protocol: str,
        tool_name: str,
        arguments: Any,
        id: str = "",
        type: str = "",
        raw_payload: Any = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> NormalizedToolCall:
        """Normalize one framework-specific tool call into the registry format."""
        parsed_arguments = _parse_arguments(arguments)
        adapter = self.resolve(protocol, tool_name)
        return NormalizedToolCall(
            id=id,
            protocol=protocol or "generic",
            type=type,
            raw_tool_name=tool_name,
            tool_name=adapter.canonical_tool_name or tool_name,
            tool_payload=parsed_arguments,
            adapter_name=adapter.name,
            extraction=adapter.extraction,
            metadata=metadata or {},
            raw_payload=raw_payload if raw_payload is not None else {},
        )

    def extract_tool_calls(self, response_payload: dict[str, Any]) -> list[ToolInvocation]:
        """Parse tool calls from supported response formats and attach adapter configs."""
        candidates = []
        candidates.extend(self._extract_openai_tool_calls(response_payload))
        candidates.extend(self._extract_content_block_tool_calls(response_payload))
        candidates.extend(self._extract_langchain_tool_calls(response_payload))
        candidates.extend(self._extract_top_level_tool_calls(response_payload))
        candidates.extend(self._extract_mcp_jsonrpc_tool_calls(response_payload))
        candidates.extend(self._extract_openai_agents_tool_calls(response_payload))

        invocations = []
        for candidate in candidates:
            invocations.append(
                self.normalize_tool_call(
                    id=candidate.id,
                    protocol=candidate.protocol,
                    type=candidate.type,
                    tool_name=candidate.raw_tool_name or candidate.tool_name,
                    arguments=candidate.tool_payload,
                    raw_payload=candidate.raw_payload,
                    metadata=candidate.metadata,
                )
            )
        return invocations

    def _extract_openai_tool_calls(self, response_payload: dict[str, Any]) -> list[ToolInvocation]:
        tool_calls = []
        for choice in response_payload.get("choices", []):
            if not isinstance(choice, dict):
                continue
            message = choice.get("message", {})
            if not isinstance(message, dict):
                continue
            raw_tool_calls = message.get("tool_calls", [])
            if not isinstance(raw_tool_calls, list):
                continue
            for tool_call in raw_tool_calls:
                if not isinstance(tool_call, dict):
                    continue
                function = tool_call.get("function", {})
                if not isinstance(function, dict):
                    continue
                tool_calls.append(
                    ToolInvocation(
                        id=str(tool_call.get("id", "")),
                        protocol="openai",
                        type=str(tool_call.get("type", "")),
                        raw_tool_name=str(function.get("name", "")),
                        tool_name=str(function.get("name", "")),
                        tool_payload=_parse_arguments(function.get("arguments", {})),
                        metadata={"framework": "openai"},
                        raw_payload=tool_call,
                    )
                )
        return tool_calls

    def _extract_content_block_tool_calls(self, response_payload: dict[str, Any]) -> list[ToolInvocation]:
        tool_calls = []
        supported_types = {"tool_use", "server_tool_use", "mcp_tool_call", "mcp_call"}
        for choice in response_payload.get("choices", []):
            if not isinstance(choice, dict):
                continue
            message = choice.get("message", {})
            if not isinstance(message, dict):
                continue
            content = message.get("content", [])
            if not isinstance(content, list):
                continue
            for item in content:
                if not isinstance(item, dict):
                    continue
                block_type = str(item.get("type", ""))
                if block_type not in supported_types:
                    continue
                tool_name = str(item.get("name") or item.get("tool_name") or "")
                protocol = "mcp" if block_type.startswith("mcp") or tool_name.startswith("mcp.") else "content_block"
                payload = item.get("input", item.get("arguments", item.get("args", {})))
                tool_calls.append(
                    ToolInvocation(
                        id=str(item.get("id", "")),
                        protocol=protocol,
                        type=block_type,
                        raw_tool_name=tool_name,
                        tool_name=tool_name,
                        tool_payload=_parse_arguments(payload),
                        metadata={"framework": protocol},
                        raw_payload=item,
                    )
                )
        return tool_calls

    def _extract_langchain_tool_calls(self, response_payload: dict[str, Any]) -> list[ToolInvocation]:
        tool_calls = []
        for choice in response_payload.get("choices", []):
            if not isinstance(choice, dict):
                continue
            message = choice.get("message", {})
            if not isinstance(message, dict):
                continue
            additional_kwargs = message.get("additional_kwargs", {})
            if not isinstance(additional_kwargs, dict):
                continue
            raw_tool_calls = additional_kwargs.get("tool_calls", [])
            if not isinstance(raw_tool_calls, list):
                continue
            for tool_call in raw_tool_calls:
                if not isinstance(tool_call, dict):
                    continue
                tool_calls.append(
                    ToolInvocation(
                        id=str(tool_call.get("id", "")),
                        protocol="langchain",
                        type=str(tool_call.get("type", "tool_call")),
                        raw_tool_name=str(tool_call.get("name", "")),
                        tool_name=str(tool_call.get("name", "")),
                        tool_payload=_parse_arguments(
                            tool_call.get("args", tool_call.get("arguments", {}))
                        ),
                        metadata={"framework": "langchain"},
                        raw_payload=tool_call,
                    )
                )
        return tool_calls

    def _extract_top_level_tool_calls(self, response_payload: dict[str, Any]) -> list[ToolInvocation]:
        tool_calls = []
        raw_tool_calls = response_payload.get("tool_calls", [])
        if not isinstance(raw_tool_calls, list):
            return tool_calls

        default_protocol = str(
            response_payload.get("protocol")
            or response_payload.get("framework")
            or response_payload.get("source")
            or "generic"
        )
        for tool_call in raw_tool_calls:
            if not isinstance(tool_call, dict):
                continue
            function = tool_call.get("function", {})
            if not isinstance(function, dict):
                function = {}
            tool_name = str(
                tool_call.get("name")
                or tool_call.get("tool_name")
                or function.get("name")
                or ""
            )
            payload = (
                function.get("arguments")
                if "arguments" in function
                else tool_call.get(
                    "arguments",
                    tool_call.get("args", tool_call.get("input", tool_call.get("kwargs", {}))),
                )
            )
            protocol = str(tool_call.get("protocol") or default_protocol)
            tool_calls.append(
                ToolInvocation(
                    id=str(tool_call.get("id", tool_call.get("call_id", ""))),
                    protocol=protocol,
                    type=str(tool_call.get("type", "tool_call")),
                    raw_tool_name=tool_name,
                    tool_name=tool_name,
                    tool_payload=_parse_arguments(payload),
                    metadata={"framework": protocol},
                    raw_payload=tool_call,
                )
            )
        return tool_calls

    def _extract_mcp_jsonrpc_tool_calls(self, response_payload: dict[str, Any]) -> list[ToolInvocation]:
        method = str(response_payload.get("method", ""))
        if method not in {"tools/call", "tool/call"}:
            return []
        params = response_payload.get("params", {})
        if not isinstance(params, dict):
            return []
        tool_name = str(params.get("name") or params.get("tool_name") or "")
        payload = params.get("arguments", params.get("args", params.get("input", {})))
        return [
            ToolInvocation(
                id=str(response_payload.get("id", "")),
                protocol="mcp",
                type=method,
                raw_tool_name=tool_name,
                tool_name=tool_name,
                tool_payload=_parse_arguments(payload),
                metadata={"framework": "mcp", "jsonrpc": str(response_payload.get("jsonrpc", ""))},
                raw_payload=response_payload,
            )
        ]

    def _extract_openai_agents_tool_calls(self, response_payload: dict[str, Any]) -> list[ToolInvocation]:
        tool_calls = []
        output = response_payload.get("output", [])
        if not isinstance(output, list):
            return tool_calls
        for item in output:
            if not isinstance(item, dict):
                continue
            item_type = str(item.get("type", ""))
            if item_type not in {"function_call", "tool_call"}:
                continue
            tool_name = str(item.get("name") or item.get("tool_name") or "")
            payload = item.get("arguments", item.get("args", item.get("input", {})))
            tool_calls.append(
                ToolInvocation(
                    id=str(item.get("call_id", item.get("id", ""))),
                    protocol="openai_agents",
                    type=item_type,
                    raw_tool_name=tool_name,
                    tool_name=tool_name,
                    tool_payload=_parse_arguments(payload),
                    metadata={"framework": "openai_agents"},
                    raw_payload=item,
                )
            )
        return tool_calls
