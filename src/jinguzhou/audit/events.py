"""Audit event models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    """Structured audit record."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: str = ""
    event_type: str = "policy_decision"
    stage: str = ""
    decision: str = ""
    policy_name: str = ""
    matched_rule_ids: list[str] = Field(default_factory=list)
    category: str = ""
    severity: str = ""
    provider: str = ""
    model: str = ""
    message: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
