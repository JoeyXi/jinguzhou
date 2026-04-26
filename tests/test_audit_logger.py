import json
from pathlib import Path

from jinguzhou.audit.events import AuditEvent
from jinguzhou.audit.logger import JsonlAuditLogger
from jinguzhou.audit.query import query_audit_events, replay_audit_events


def test_jsonl_logger_writes_event(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.jsonl"
    logger = JsonlAuditLogger(log_path)

    logger.write(
        AuditEvent(
            request_id="req-1",
            decision="block",
            policy_name="baseline-human-safety",
            message="blocked secret sk-1234567890abcdefghijklmnop",
        )
    )

    raw = log_path.read_text(encoding="utf-8").strip()
    payload = json.loads(raw)
    assert payload["request_id"] == "req-1"
    assert "[REDACTED]" in payload["message"]


def test_audit_query_and_replay(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.jsonl"
    logger = JsonlAuditLogger(log_path)
    logger.write(
        AuditEvent(
            request_id="req-1",
            stage="input",
            decision="allow",
            message="ok",
        )
    )
    logger.write(
        AuditEvent(
            request_id="req-2",
            stage="tool",
            decision="require_human_review",
            matched_rule_ids=["tool.shell.destructive.require_review"],
            message="review",
        )
    )

    results = query_audit_events(log_path, stage="tool", rule_id="tool.shell.destructive.require_review")
    replay = replay_audit_events(log_path, request_id="req-2")

    assert len(results) == 1
    assert results[0].request_id == "req-2"
    assert "stage=tool" in replay[0]
