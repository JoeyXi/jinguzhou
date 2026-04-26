"""Audit log query and replay helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

from jinguzhou.audit.events import AuditEvent


def iter_audit_events(path: Path) -> Iterable[AuditEvent]:
    """Yield audit events from a JSONL file."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        yield AuditEvent.model_validate(json.loads(line))


def query_audit_events(
    path: Path,
    *,
    request_id: str = "",
    stage: str = "",
    decision: str = "",
    rule_id: str = "",
    limit: Optional[int] = None,
) -> list[AuditEvent]:
    """Filter audit events by common safety-review dimensions."""
    results = []
    for event in iter_audit_events(path):
        if request_id and event.request_id != request_id:
            continue
        if stage and event.stage != stage:
            continue
        if decision and event.decision != decision:
            continue
        if rule_id and rule_id not in event.matched_rule_ids:
            continue
        results.append(event)

    if limit is not None and limit >= 0:
        return results[-limit:]
    return results


def replay_audit_events(path: Path, *, request_id: str = "") -> list[str]:
    """Render a compact request timeline from audit events."""
    events = query_audit_events(path, request_id=request_id)
    lines = []
    for event in events:
        rule_text = ",".join(event.matched_rule_ids) if event.matched_rule_ids else "-"
        lines.append(
            f"{event.timestamp.isoformat()} request={event.request_id or '-'} "
            f"stage={event.stage or '-'} decision={event.decision or '-'} "
            f"rules={rule_text} message={event.message}"
        )
    return lines
