"""Postgres audit logger."""

from __future__ import annotations

import json
import re
from typing import Any

from jinguzhou.audit.events import AuditEvent
from jinguzhou.audit.redaction import redact_text

IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class PostgresAuditLogger:
    """Append audit events to a Postgres table.

    This backend requires the optional `psycopg` package. Install with:

        pip install "jinguzhou[postgres]"
    """

    def __init__(self, dsn: str, *, table: str = "jinguzhou_audit_events", redact: bool = True) -> None:
        if not dsn:
            raise ValueError("Postgres audit backend requires audit.postgres_dsn.")
        if not IDENTIFIER_RE.fullmatch(table):
            raise ValueError("audit.postgres_table must be a simple SQL identifier.")
        self.dsn = dsn
        self.table = table
        self.redact = redact
        self._ensure_table()

    def _connect(self) -> Any:
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError(
                "Postgres audit backend requires psycopg. "
                'Install it with: pip install "jinguzhou[postgres]"'
            ) from exc
        return psycopg.connect(self.dsn)

    def _ensure_table(self) -> None:
        statement = f"""
        CREATE TABLE IF NOT EXISTS {self.table} (
            event_id TEXT PRIMARY KEY,
            timestamp TIMESTAMPTZ NOT NULL,
            request_id TEXT NOT NULL,
            stage TEXT NOT NULL,
            decision TEXT NOT NULL,
            payload JSONB NOT NULL
        )
        """
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(statement)
            conn.commit()

    def write(self, event: AuditEvent) -> None:
        """Append a serialized audit event to Postgres."""
        payload = event.model_dump(mode="json")
        if self.redact and payload.get("message"):
            payload["message"] = redact_text(str(payload["message"]))
        event = AuditEvent.model_validate(payload)
        statement = f"""
        INSERT INTO {self.table} (
            event_id, timestamp, request_id, stage, decision, payload
        ) VALUES (%s, %s, %s, %s, %s, %s::jsonb)
        """
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    statement,
                    (
                        event.event_id,
                        event.timestamp,
                        event.request_id,
                        event.stage,
                        event.decision,
                        json.dumps(event.model_dump(mode="json"), sort_keys=True),
                    ),
                )
            conn.commit()
