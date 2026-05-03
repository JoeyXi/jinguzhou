import json
from pathlib import Path

from jinguzhou.approvals.tokens import ApprovalTokenManager
from jinguzhou.audit.logger import JsonlAuditLogger
from jinguzhou.integrations.llamaindex import (
    JinguzhouLlamaIndexMiddleware,
    ToolPolicyViolation,
    guard_tool,
)
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_file


class _Metadata:
    name = "filesystem.write"


class FakeLlamaIndexTool:
    metadata = _Metadata()

    def __init__(self) -> None:
        self.called = False

    def call(self, input, **kwargs):
        self.called = True
        return {"path": input["path"], "status": "ok"}


def _read_events(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_llamaindex_guard_requires_approval_for_user_data_write(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    manager = ApprovalTokenManager("llamaindex-secret")
    middleware = JinguzhouLlamaIndexMiddleware(
        PolicyEngine(load_policy_file(Path("rules/tool_file_access.yaml"))),
        audit_logger=JsonlAuditLogger(audit_path),
        approval_manager=manager,
    )
    tool = FakeLlamaIndexTool()
    guarded = guard_tool(tool, middleware)

    try:
        guarded.call(
            {"path": "/Users/demo/Documents/report.txt", "content": "demo"},
            jinguzhou_request_id="req-llamaindex-review",
        )
    except ToolPolicyViolation as exc:
        assert exc.result.action == "require_human_review"
    else:
        raise AssertionError("Expected approval requirement.")

    assert tool.called is False

    token = manager.issue(
        request_id="req-llamaindex-review",
        stage="tool",
        rule_ids=["tool.file.user_data_write.review"],
        approver="alice",
    )
    result = guarded.call(
        {"path": "/Users/demo/Documents/report.txt", "content": "demo"},
        jinguzhou_request_id="req-llamaindex-review",
        jinguzhou_approval_token=token,
    )

    assert result["status"] == "ok"
    assert tool.called is True

    events = _read_events(audit_path)
    assert events[-1]["event_type"] == "approval"
    assert events[-1]["decision"] == "approved"
