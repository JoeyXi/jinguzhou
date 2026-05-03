"""LlamaIndex-style tool middleware."""

from __future__ import annotations

import inspect
from typing import Any, Optional

from jinguzhou.approvals.tokens import ApprovalTokenManager
from jinguzhou.gateway.middleware import (
    ToolFirewallDecision,
    ToolFirewallMiddleware,
    ToolPolicyViolation,
)
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.models import EvaluationResult
from jinguzhou.tools.adapters import NormalizedToolCall, ToolAdapterRegistry


class JinguzhouLlamaIndexMiddleware(ToolFirewallMiddleware):
    """Evaluate LlamaIndex-style tool calls before execution."""

    def __init__(
        self,
        policy_engine: PolicyEngine,
        *,
        registry: Optional[ToolAdapterRegistry] = None,
        audit_logger: Optional[Any] = None,
        approval_manager: Optional[ApprovalTokenManager] = None,
        model: str = "",
        provider: str = "llamaindex",
    ) -> None:
        super().__init__(
            policy_engine,
            registry=registry,
            audit_logger=audit_logger,
            approval_manager=approval_manager,
            model=model,
            provider=provider,
            framework="llamaindex",
        )

    def normalize(self, tool_name: str, arguments: Any) -> NormalizedToolCall:
        return self.normalize_tool_call(
            protocol="llamaindex",
            tool_name=tool_name,
            arguments=arguments,
            type="tool_call",
            metadata={"framework": "llamaindex"},
        )

    def check_call(
        self,
        tool_name: str,
        arguments: Any,
        *,
        approval_token: str = "",
        request_id: str = "",
    ) -> ToolFirewallDecision:
        return self.evaluate_tool_call(
            self.normalize(tool_name, arguments),
            request_id=request_id,
            approval_token=approval_token,
            metadata={"framework": "llamaindex"},
        )

    def check(
        self,
        tool_name: str,
        arguments: Any,
        *,
        approval_token: str = "",
        request_id: str = "",
    ) -> EvaluationResult:
        return self.check_call(
            tool_name,
            arguments,
            approval_token=approval_token,
            request_id=request_id,
        ).result


class GuardedLlamaIndexTool:
    """Wrapper for LlamaIndex-like tool objects."""

    def __init__(self, tool: Any, middleware: JinguzhouLlamaIndexMiddleware) -> None:
        self._tool = tool
        self._middleware = middleware

    def __getattr__(self, name: str) -> Any:
        return getattr(self._tool, name)

    @property
    def name(self) -> str:
        metadata = getattr(self._tool, "metadata", None)
        metadata_name = getattr(metadata, "name", "")
        if metadata_name:
            return str(metadata_name)
        name = getattr(self._tool, "name", "")
        if name:
            return str(name)
        function_name = getattr(self._tool, "__name__", "")
        if function_name:
            return str(function_name)
        return self._tool.__class__.__name__

    def call(self, input: Any, **kwargs: Any) -> Any:
        approval_token = str(kwargs.pop("jinguzhou_approval_token", ""))
        request_id = str(kwargs.pop("jinguzhou_request_id", ""))
        self._middleware.check(
            self.name,
            input,
            approval_token=approval_token,
            request_id=request_id,
        )
        if hasattr(self._tool, "call"):
            return self._tool.call(input, **kwargs)
        if hasattr(self._tool, "invoke"):
            return self._tool.invoke(input, **kwargs)
        if callable(self._tool):
            return self._tool(input, **kwargs)
        raise TypeError("Wrapped tool does not expose call, invoke, or callable behavior.")

    async def acall(self, input: Any, **kwargs: Any) -> Any:
        approval_token = str(kwargs.pop("jinguzhou_approval_token", ""))
        request_id = str(kwargs.pop("jinguzhou_request_id", ""))
        self._middleware.check(
            self.name,
            input,
            approval_token=approval_token,
            request_id=request_id,
        )
        if hasattr(self._tool, "acall"):
            return await self._tool.acall(input, **kwargs)
        result = self.call(input, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result

    def invoke(self, input: Any, **kwargs: Any) -> Any:
        return self.call(input, **kwargs)

    def __call__(self, input: Any, **kwargs: Any) -> Any:
        return self.call(input, **kwargs)


def guard_tool(tool: Any, middleware: JinguzhouLlamaIndexMiddleware) -> GuardedLlamaIndexTool:
    """Wrap a LlamaIndex-style tool with Jinguzhou policy checks."""
    return GuardedLlamaIndexTool(tool, middleware)


__all__ = [
    "GuardedLlamaIndexTool",
    "JinguzhouLlamaIndexMiddleware",
    "ToolFirewallDecision",
    "ToolPolicyViolation",
    "guard_tool",
]
