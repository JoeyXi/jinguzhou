"""LangChain-style tool middleware.

The module avoids importing LangChain directly. It wraps objects that expose the
usual `name`, `invoke`, `ainvoke`, `run`, or callable interfaces.
"""

from __future__ import annotations

import inspect
from typing import Any, Callable, Optional

from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.models import EvaluationContext, EvaluationResult
from jinguzhou.tools.adapters import NormalizedToolCall, ToolAdapterRegistry


BLOCKING_ACTIONS = {"block", "require_human_review"}


class ToolPolicyViolation(RuntimeError):
    """Raised when policy prevents a LangChain-style tool from executing."""

    def __init__(self, result: EvaluationResult, tool_call: NormalizedToolCall) -> None:
        super().__init__(result.summary)
        self.result = result
        self.tool_call = tool_call


class JinguzhouToolMiddleware:
    """Evaluate LangChain-style tool calls before the wrapped tool executes."""

    def __init__(
        self,
        policy_engine: PolicyEngine,
        *,
        registry: Optional[ToolAdapterRegistry] = None,
        model: str = "",
        provider: str = "langchain",
    ) -> None:
        self.policy_engine = policy_engine
        self.registry = registry or ToolAdapterRegistry.with_defaults()
        self.model = model
        self.provider = provider

    def normalize(self, tool_name: str, arguments: Any) -> NormalizedToolCall:
        """Normalize a LangChain tool invocation."""
        return self.registry.normalize_tool_call(
            protocol="langchain",
            tool_name=tool_name,
            arguments=arguments,
            type="tool_call",
            metadata={"framework": "langchain"},
        )

    def check(self, tool_name: str, arguments: Any) -> EvaluationResult:
        """Evaluate a tool invocation and raise when policy blocks execution."""
        tool_call = self.normalize(tool_name, arguments)
        result = self.policy_engine.evaluate(
            EvaluationContext(
                stage="tool",
                tool_name=tool_call.tool_name,
                tool_payload=tool_call.arguments,
                model=self.model,
                provider=self.provider,
                tool_extraction=tool_call.extraction,
            )
        )
        if result.action in BLOCKING_ACTIONS:
            raise ToolPolicyViolation(result, tool_call)
        return result

    def invoke(
        self,
        tool_name: str,
        arguments: Any,
        execute: Callable[[Any], Any],
    ) -> Any:
        """Check policy and run a synchronous tool executor."""
        self.check(tool_name, arguments)
        return execute(arguments)

    async def ainvoke(
        self,
        tool_name: str,
        arguments: Any,
        execute: Callable[[Any], Any],
    ) -> Any:
        """Check policy and run an async or sync tool executor."""
        self.check(tool_name, arguments)
        result = execute(arguments)
        if inspect.isawaitable(result):
            return await result
        return result


class GuardedLangChainTool:
    """Small wrapper for LangChain-like tool objects."""

    def __init__(self, tool: Any, middleware: JinguzhouToolMiddleware) -> None:
        self._tool = tool
        self._middleware = middleware

    def __getattr__(self, name: str) -> Any:
        return getattr(self._tool, name)

    @property
    def name(self) -> str:
        return _tool_name(self._tool)

    def invoke(self, input: Any, config: Any = None, **kwargs: Any) -> Any:
        """Guard and invoke a LangChain-style tool."""
        self._middleware.check(self.name, input)
        if hasattr(self._tool, "invoke"):
            return self._tool.invoke(input, config=config, **kwargs)
        if callable(self._tool):
            if config is None:
                return self._tool(input, **kwargs)
            return self._tool(input, config=config, **kwargs)
        raise TypeError("Wrapped tool does not expose invoke or callable behavior.")

    async def ainvoke(self, input: Any, config: Any = None, **kwargs: Any) -> Any:
        """Guard and invoke an async LangChain-style tool."""
        self._middleware.check(self.name, input)
        if hasattr(self._tool, "ainvoke"):
            return await self._tool.ainvoke(input, config=config, **kwargs)
        result = self.invoke(input, config=config, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result

    def run(self, input: Any, **kwargs: Any) -> Any:
        """Guard and run tools that expose LangChain's older `run` method."""
        self._middleware.check(self.name, input)
        if hasattr(self._tool, "run"):
            return self._tool.run(input, **kwargs)
        return self.invoke(input, **kwargs)

    def __call__(self, input: Any, **kwargs: Any) -> Any:
        return self.invoke(input, **kwargs)


def _tool_name(tool: Any) -> str:
    name = getattr(tool, "name", "")
    if name:
        return str(name)
    function_name = getattr(tool, "__name__", "")
    if function_name:
        return str(function_name)
    return tool.__class__.__name__


def guard_tool(tool: Any, middleware: JinguzhouToolMiddleware) -> GuardedLangChainTool:
    """Wrap a LangChain-style tool with Jinguzhou policy checks."""
    return GuardedLangChainTool(tool, middleware)
