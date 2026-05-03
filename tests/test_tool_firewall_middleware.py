import json
from pathlib import Path

import pytest

from jinguzhou.approvals.tokens import ApprovalTokenManager
from jinguzhou.audit.logger import JsonlAuditLogger
from jinguzhou.gateway.middleware import ToolFirewallMiddleware, ToolPolicyViolation
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_file


def _read_events(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_shared_tool_firewall_blocks_and_audits(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    middleware = ToolFirewallMiddleware(
        PolicyEngine(load_policy_file(Path("rules/tool_file_access.yaml"))),
        audit_logger=JsonlAuditLogger(audit_path),
        provider="shared-test",
    )
    tool_call = middleware.normalize_tool_call(
        protocol="generic",
        tool_name="filesystem.write",
        arguments={"path": "/etc/hosts", "content": "demo"},
    )

    with pytest.raises(ToolPolicyViolation) as exc:
        middleware.evaluate_tool_call(tool_call, request_id="req-shared-block")

    assert exc.value.result.action == "block"
    events = _read_events(audit_path)
    assert len(events) == 1
    assert events[0]["event_type"] == "policy_decision"
    assert events[0]["decision"] == "block"
    assert events[0]["metadata"]["tool_name"] == "filesystem.write"


def test_shared_tool_firewall_accepts_approval_and_writes_audit(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    manager = ApprovalTokenManager("shared-secret")
    middleware = ToolFirewallMiddleware(
        PolicyEngine(load_policy_file(Path("rules/tool_use.yaml"))),
        audit_logger=JsonlAuditLogger(audit_path),
        approval_manager=manager,
        provider="shared-test",
    )
    tool_call = middleware.normalize_tool_call(
        protocol="generic",
        tool_name="shell",
        arguments={"command": "rm -rf /tmp/demo"},
    )

    token = manager.issue(
        request_id="req-shared-review",
        stage="tool",
        rule_ids=["tool.shell.destructive.require_review"],
        approver="alice",
    )
    decision = middleware.evaluate_tool_call(
        tool_call,
        request_id="req-shared-review",
        approval_token=token,
    )

    assert decision.result.action == "require_human_review"
    assert decision.approval_claims is not None
    assert decision.approval_claims.approver == "alice"

    events = _read_events(audit_path)
    assert [event["event_type"] for event in events] == ["policy_decision", "approval"]
    assert events[-1]["decision"] == "approved"
