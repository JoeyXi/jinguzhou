import sys
from types import SimpleNamespace

import pytest

from jinguzhou.audit.events import AuditEvent
from jinguzhou.audit.postgres import PostgresAuditLogger


class FakeCursor:
    def __init__(self, calls: list[tuple[str, object]]) -> None:
        self.calls = calls

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def execute(self, statement: str, params: object = None) -> None:
        self.calls.append((statement, params))


class FakeConnection:
    def __init__(self, calls: list[tuple[str, object]]) -> None:
        self.calls = calls
        self.commits = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def cursor(self) -> FakeCursor:
        return FakeCursor(self.calls)

    def commit(self) -> None:
        self.commits += 1


def test_postgres_audit_logger_writes_event(monkeypatch) -> None:
    calls: list[tuple[str, object]] = []

    def connect(dsn: str) -> FakeConnection:
        assert dsn == "postgresql://localhost/jinguzhou"
        return FakeConnection(calls)

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=connect))

    logger = PostgresAuditLogger("postgresql://localhost/jinguzhou")
    logger.write(AuditEvent(request_id="req-1", stage="input", decision="allow", message="ok"))

    statements = [call[0] for call in calls]
    assert any("CREATE TABLE IF NOT EXISTS jinguzhou_audit_events" in item for item in statements)
    assert any("INSERT INTO jinguzhou_audit_events" in item for item in statements)


def test_postgres_audit_logger_rejects_unsafe_table_name() -> None:
    with pytest.raises(ValueError, match="simple SQL identifier"):
        PostgresAuditLogger("postgresql://localhost/jinguzhou", table="audit;drop")
