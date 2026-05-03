import asyncio
import json
from pathlib import Path

from jinguzhou.approvals.tokens import ApprovalTokenManager
from jinguzhou.audit.logger import JsonlAuditLogger
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


def _read_events(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


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


def test_langchain_guard_supports_approval_and_audit(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    manager = ApprovalTokenManager("langchain-secret")
    policy = load_policy_file(Path("rules/tool_file_access.yaml"))
    middleware = JinguzhouToolMiddleware(
        PolicyEngine(policy),
        audit_logger=JsonlAuditLogger(audit_path),
        approval_manager=manager,
    )
    tool = FakeReadTool()
    guarded = guard_tool(tool, middleware)
    token = manager.issue(
        request_id="req-langchain-review",
        stage="tool",
        rule_ids=["tool.file.secret_path.review"],
        approver="alice",
    )

    result = guarded.invoke(
        {"path": "/Users/demo/.ssh/id_rsa"},
        jinguzhou_request_id="req-langchain-review",
        jinguzhou_approval_token=token,
    )

    assert result["path"] == "/Users/demo/.ssh/id_rsa"
    assert tool.called is True

    events = _read_events(audit_path)
    assert [event["event_type"] for event in events] == ["policy_decision", "approval"]
    assert events[-1]["decision"] == "approved"
