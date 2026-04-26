"""JSONL audit logger."""

from __future__ import annotations

from pathlib import Path

from jinguzhou.audit.events import AuditEvent
from jinguzhou.audit.redaction import redact_text


class JsonlAuditLogger:
    """Append-only JSONL logger for audit events."""

    def __init__(self, path: Path, redact: bool = True) -> None:
        self.path = path
        self.redact = redact
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event: AuditEvent) -> None:
        """Append a serialized audit event to disk."""
        payload = event.model_dump(mode="json")
        if self.redact and payload.get("message"):
            payload["message"] = redact_text(str(payload["message"]))
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(AuditEvent.model_validate(payload).model_dump_json())
            handle.write("\n")

