"""MCP runtime middleware."""

from __future__ import annotations

import inspect
from typing import Any, Callable, Optional

from jinguzhou.adapters.mcp import MCPToolAdapter
from jinguzhou.approvals.tokens import ApprovalTokenManager
from jinguzhou.gateway.middleware import (
    ToolFirewallDecision,
    ToolFirewallMiddleware,
    ToolPolicyViolation,
)
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.tools.adapters import ToolAdapterRegistry


class JinguzhouMCPMiddleware(ToolFirewallMiddleware):
    """Evaluate MCP JSON-RPC tool calls before a runtime executes them."""

    def __init__(
        self,
        policy_engine: PolicyEngine,
        *,
        registry: Optional[ToolAdapterRegistry] = None,
        audit_logger: Optional[Any] = None,
        approval_manager: Optional[ApprovalTokenManager] = None,
        model: str = "",
        provider: str = "mcp",
    ) -> None:
        super().__init__(
            policy_engine,
            registry=registry,
            audit_logger=audit_logger,
            approval_manager=approval_manager,
            model=model,
            provider=provider,
            framework="mcp",
        )
        self.adapter = MCPToolAdapter(self.registry)

    def normalize_request(self, payload: dict[str, Any]) -> Any:
        return self.adapter.normalize_jsonrpc_request(payload)

    def check_request(
        self,
        payload: dict[str, Any],
        *,
        approval_token: str = "",
        request_id: str = "",
    ) -> ToolFirewallDecision:
        tool_call = self.normalize_request(payload)
        return self.evaluate_tool_call(
            tool_call,
            request_id=request_id,
            approval_token=approval_token,
            metadata={"framework": "mcp", "method": str(payload.get("method", ""))},
        )

    def handle_request(
        self,
        payload: dict[str, Any],
        execute: Callable[[dict[str, Any]], Any],
        *,
        approval_token: str = "",
        request_id: str = "",
    ) -> Any:
        self.check_request(payload, approval_token=approval_token, request_id=request_id)
        return execute(payload)

    async def ahandle_request(
        self,
        payload: dict[str, Any],
        execute: Callable[[dict[str, Any]], Any],
        *,
        approval_token: str = "",
        request_id: str = "",
    ) -> Any:
        self.check_request(payload, approval_token=approval_token, request_id=request_id)
        result = execute(payload)
        if inspect.isawaitable(result):
            return await result
        return result


class GuardedMCPRuntime:
    """Small wrapper around an MCP request executor."""

    def __init__(
        self,
        execute: Callable[[dict[str, Any]], Any],
        middleware: JinguzhouMCPMiddleware,
    ) -> None:
        self._execute = execute
        self._middleware = middleware

    def handle(
        self,
        payload: dict[str, Any],
        *,
        approval_token: str = "",
        request_id: str = "",
    ) -> Any:
        return self._middleware.handle_request(
            payload,
            self._execute,
            approval_token=approval_token,
            request_id=request_id,
        )

    async def ahandle(
        self,
        payload: dict[str, Any],
        *,
        approval_token: str = "",
        request_id: str = "",
    ) -> Any:
        return await self._middleware.ahandle_request(
            payload,
            self._execute,
            approval_token=approval_token,
            request_id=request_id,
        )


def guard_runtime(
    execute: Callable[[dict[str, Any]], Any],
    middleware: JinguzhouMCPMiddleware,
) -> GuardedMCPRuntime:
    """Wrap an MCP request executor with Jinguzhou policy checks."""
    return GuardedMCPRuntime(execute, middleware)


__all__ = [
    "GuardedMCPRuntime",
    "JinguzhouMCPMiddleware",
    "ToolFirewallDecision",
    "ToolPolicyViolation",
    "guard_runtime",
]
