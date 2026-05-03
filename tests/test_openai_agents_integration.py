import json
from pathlib import Path

from jinguzhou.approvals.tokens import ApprovalTokenManager
from jinguzhou.audit.logger import JsonlAuditLogger
from jinguzhou.integrations.openai_agents import (
    JinguzhouOpenAIAgentsMiddleware,
    ToolPolicyViolation,
    guard_function_tool,
)
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_file


def _read_events(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_openai_agents_guard_blocks_destructive_sql(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    middleware = JinguzhouOpenAIAgentsMiddleware(
        PolicyEngine(load_policy_file(Path("rules/tool_database_access.yaml"))),
        audit_logger=JsonlAuditLogger(audit_path),
    )
    called = {"value": False}

    def tool(arguments):
        called["value"] = True
        return {"ok": True, "sql": arguments["sql"]}

    guarded = guard_function_tool("db.run_sql", tool, middleware)

    try:
        guarded({"sql": "DROP TABLE users"})
    except ToolPolicyViolation as exc:
        assert exc.result.action == "block"
    else:
        raise AssertionError("Expected destructive SQL to be blocked.")

    assert called["value"] is False


def test_openai_agents_guard_supports_approval_and_audit(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    manager = ApprovalTokenManager("agents-secret")
    middleware = JinguzhouOpenAIAgentsMiddleware(
        PolicyEngine(load_policy_file(Path("rules/tool_database_access.yaml"))),
        audit_logger=JsonlAuditLogger(audit_path),
        approval_manager=manager,
    )

    def tool(arguments):
        return {"sql": arguments["sql"], "status": "executed"}

    guarded = guard_function_tool("db.run_sql", tool, middleware)
    token = manager.issue(
        request_id="req-openai-agents-review",
        stage="tool",
        rule_ids=["tool.database.mutation.review"],
        approver="alice",
    )
    result = guarded(
        {"sql": "UPDATE users SET role = 'admin'"},
        jinguzhou_request_id="req-openai-agents-review",
        jinguzhou_approval_token=token,
    )

    assert result["status"] == "executed"
    events = _read_events(audit_path)
    assert [event["event_type"] for event in events] == ["policy_decision", "approval"]
    assert events[-1]["decision"] == "approved"
