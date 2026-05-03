import json
from pathlib import Path

from jinguzhou.adapters.mcp import build_mcp_tool_call_request
from jinguzhou.approvals.tokens import ApprovalTokenManager
from jinguzhou.audit.logger import JsonlAuditLogger
from jinguzhou.integrations.mcp import JinguzhouMCPMiddleware, ToolPolicyViolation, guard_runtime
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_file


def _read_events(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_mcp_runtime_guard_blocks_before_execution(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    middleware = JinguzhouMCPMiddleware(
        PolicyEngine(load_policy_file(Path("rules/tool_network_access.yaml"))),
        audit_logger=JsonlAuditLogger(audit_path),
    )
    called = {"value": False}

    def execute(request):
        called["value"] = True
        return {"ok": True, "id": request["id"]}

    runtime = guard_runtime(execute, middleware)
    request = build_mcp_tool_call_request(
        "mcp.fetch.get",
        {"request": {"url": "http://169.254.169.254/latest/meta-data"}},
        call_id="mcp-metadata",
    )

    try:
        runtime.handle(request, request_id="req-mcp-block")
    except ToolPolicyViolation as exc:
        assert exc.result.action == "block"
    else:
        raise AssertionError("Expected metadata endpoint request to be blocked.")

    assert called["value"] is False


def test_mcp_runtime_guard_supports_approval_and_audit(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    manager = ApprovalTokenManager("mcp-secret")
    middleware = JinguzhouMCPMiddleware(
        PolicyEngine(load_policy_file(Path("rules/tool_network_access.yaml"))),
        audit_logger=JsonlAuditLogger(audit_path),
        approval_manager=manager,
    )

    def execute(request):
        return {"ok": True, "id": request["id"]}

    runtime = guard_runtime(execute, middleware)
    request = build_mcp_tool_call_request(
        "mcp.fetch.get",
        {"request": {"url": "https://demo.ngrok.io/api"}},
        call_id="mcp-ngrok-review",
    )
    token = manager.issue(
        request_id="req-mcp-review",
        stage="tool",
        rule_ids=["tool.network.public_tunnel.review"],
        approver="alice",
    )

    result = runtime.handle(
        request,
        request_id="req-mcp-review",
        approval_token=token,
    )

    assert result["ok"] is True
    events = _read_events(audit_path)
    assert [event["event_type"] for event in events] == ["policy_decision", "approval"]
    assert events[-1]["decision"] == "approved"
