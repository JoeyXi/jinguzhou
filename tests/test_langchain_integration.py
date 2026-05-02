import asyncio
from pathlib import Path

from jinguzhou.integrations.langchain import (
    JinguzhouToolMiddleware,
    ToolPolicyViolation,
    guard_tool,
)
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_file


class FakeWriteTool:
    name = "filesystem.write"

    def __init__(self) -> None:
        self.called = False

    def invoke(self, input, config=None):
        self.called = True
        return {"path": input["path"]}


class FakeReadTool:
    name = "filesystem.read"

    def __init__(self) -> None:
        self.called = False

    def invoke(self, input, config=None):
        self.called = True
        return {"path": input["path"], "content": "demo"}

    async def ainvoke(self, input, config=None):
        self.called = True
        return {"path": input["path"], "content": "demo"}


def _middleware() -> JinguzhouToolMiddleware:
    policy = load_policy_file(Path("rules/tool_file_access.yaml"))
    return JinguzhouToolMiddleware(PolicyEngine(policy))


def test_langchain_guard_blocks_before_tool_executes() -> None:
    tool = FakeWriteTool()
    guarded = guard_tool(tool, _middleware())

    try:
        guarded.invoke({"path": "/etc/hosts", "content": "demo"})
    except ToolPolicyViolation as exc:
        assert exc.result.action == "block"
        assert exc.result.matched_rules[0].rule_id == "tool.file.system_write.block"
    else:
        raise AssertionError("Expected policy violation.")

    assert tool.called is False


def test_langchain_guard_allows_safe_tool_execution() -> None:
    tool = FakeReadTool()
    guarded = guard_tool(tool, _middleware())

    result = guarded.invoke({"path": "README.md"})

    assert result == {"path": "README.md", "content": "demo"}
    assert tool.called is True


def test_langchain_guard_supports_async_invoke() -> None:
    async def run_case():
        tool = FakeReadTool()
        guarded = guard_tool(tool, _middleware())

        result = await guarded.ainvoke({"path": "README.md"})

        assert result == {"path": "README.md", "content": "demo"}
        assert tool.called is True

    asyncio.run(run_case())
