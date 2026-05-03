"""OpenAI Agents-style tool middleware."""

from __future__ import annotations

import inspect
from typing import Any, Callable, Optional

from jinguzhou.approvals.tokens import ApprovalTokenManager
from jinguzhou.gateway.middleware import (
    ToolFirewallDecision,
    ToolFirewallMiddleware,
    ToolPolicyViolation,
)
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.models import EvaluationResult
from jinguzhou.tools.adapters import NormalizedToolCall, ToolAdapterRegistry


class JinguzhouOpenAIAgentsMiddleware(ToolFirewallMiddleware):
    """Evaluate OpenAI Agents-style function calls before execution."""

    def __init__(
        self,
        policy_engine: PolicyEngine,
        *,
        registry: Optional[ToolAdapterRegistry] = None,
        audit_logger: Optional[Any] = None,
        approval_manager: Optional[ApprovalTokenManager] = None,
        model: str = "",
        provider: str = "openai_agents",
    ) -> None:
        super().__init__(
            policy_engine,
            registry=registry,
            audit_logger=audit_logger,
            approval_manager=approval_manager,
            model=model,
            provider=provider,
            framework="openai_agents",
        )

    def normalize_function_call(
        self,
        name: str,
        arguments: Any,
        *,
        call_id: str = "",
        raw_payload: Any = None,
    ) -> NormalizedToolCall:
        return self.normalize_tool_call(
            protocol="openai_agents",
            tool_name=name,
            arguments=arguments,
            call_id=call_id,
            type="function_call",
            raw_payload=raw_payload,
            metadata={"framework": "openai_agents"},
        )

    def check_function_call(
        self,
        name: str,
        arguments: Any,
        *,
        approval_token: str = "",
        request_id: str = "",
        call_id: str = "",
        raw_payload: Any = None,
    ) -> ToolFirewallDecision:
        return self.evaluate_tool_call(
            self.normalize_function_call(name, arguments, call_id=call_id, raw_payload=raw_payload),
            request_id=request_id,
            approval_token=approval_token,
            metadata={"framework": "openai_agents"},
        )

    def check(
        self,
        name: str,
        arguments: Any,
        *,
        approval_token: str = "",
        request_id: str = "",
        call_id: str = "",
        raw_payload: Any = None,
    ) -> EvaluationResult:
        return self.check_function_call(
            name,
            arguments,
            approval_token=approval_token,
            request_id=request_id,
            call_id=call_id,
            raw_payload=raw_payload,
        ).result


class GuardedOpenAIAgentsTool:
    """Wrap a callable used as an OpenAI Agents tool."""

    def __init__(
        self,
        tool_name: str,
        tool: Callable[..., Any],
        middleware: JinguzhouOpenAIAgentsMiddleware,
    ) -> None:
        self.name = tool_name
        self._tool = tool
        self._middleware = middleware

    def __call__(self, arguments: Any, **kwargs: Any) -> Any:
        approval_token = str(kwargs.pop("jinguzhou_approval_token", ""))
        request_id = str(kwargs.pop("jinguzhou_request_id", ""))
        self._middleware.check(
            self.name,
            arguments,
            approval_token=approval_token,
            request_id=request_id,
        )
        return self._tool(arguments, **kwargs)

    async def ainvoke(self, arguments: Any, **kwargs: Any) -> Any:
        approval_token = str(kwargs.pop("jinguzhou_approval_token", ""))
        request_id = str(kwargs.pop("jinguzhou_request_id", ""))
        self._middleware.check(
            self.name,
            arguments,
            approval_token=approval_token,
            request_id=request_id,
        )
        result = self._tool(arguments, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result


def guard_function_tool(
    tool_name: str,
    tool: Callable[..., Any],
    middleware: JinguzhouOpenAIAgentsMiddleware,
) -> GuardedOpenAIAgentsTool:
    """Wrap an OpenAI Agents-style tool callable with Jinguzhou checks."""
    return GuardedOpenAIAgentsTool(tool_name, tool, middleware)


__all__ = [
    "GuardedOpenAIAgentsTool",
    "JinguzhouOpenAIAgentsMiddleware",
    "ToolFirewallDecision",
    "ToolPolicyViolation",
    "guard_function_tool",
]
