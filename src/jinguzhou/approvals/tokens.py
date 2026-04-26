"""Signed approval tokens for human-review decisions."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


class ApprovalClaims(BaseModel):
    """Claims signed into an approval token."""

    approval_id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str
    stage: str
    rule_ids: list[str] = Field(default_factory=list)
    approver: str = ""
    reason: str = ""
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime


class ApprovalTokenManager:
    """HMAC-signed approval token issuer and verifier."""

    def __init__(self, secret: str) -> None:
        self.secret = secret

    def issue(
        self,
        *,
        request_id: str,
        stage: str,
        rule_ids: list[str],
        approver: str = "",
        reason: str = "",
        ttl_seconds: int = 900,
    ) -> str:
        """Issue a signed approval token."""
        claims = ApprovalClaims(
            request_id=request_id,
            stage=stage,
            rule_ids=sorted(rule_ids),
            approver=approver,
            reason=reason,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds),
        )
        encoded_payload = _b64encode(claims.model_dump_json().encode("utf-8"))
        signature = self._sign(encoded_payload)
        return f"{encoded_payload}.{signature}"

    def decode(self, token: str) -> ApprovalClaims:
        """Verify and decode a token."""
        encoded_payload, signature = token.split(".", maxsplit=1)
        expected = self._sign(encoded_payload)
        if not hmac.compare_digest(signature, expected):
            raise ValueError("Invalid approval token signature.")
        payload = json.loads(_b64decode(encoded_payload).decode("utf-8"))
        claims = ApprovalClaims.model_validate(payload)
        if claims.expires_at < datetime.now(timezone.utc):
            raise ValueError("Approval token has expired.")
        return claims

    def allows(
        self,
        token: str,
        *,
        request_id: str,
        stage: str,
        rule_ids: list[str],
    ) -> ApprovalClaims:
        """Verify that a token approves the given decision."""
        claims = self.decode(token)
        if claims.request_id not in {request_id, "*"}:
            raise ValueError("Approval token request_id does not match.")
        if claims.stage not in {stage, "*"}:
            raise ValueError("Approval token stage does not match.")
        approved_rule_ids = set(claims.rule_ids)
        requested_rule_ids = set(rule_ids)
        if approved_rule_ids and not requested_rule_ids.issubset(approved_rule_ids):
            raise ValueError("Approval token rule_ids do not match.")
        return claims

    def _sign(self, encoded_payload: str) -> str:
        digest = hmac.new(
            self.secret.encode("utf-8"),
            encoded_payload.encode("ascii"),
            hashlib.sha256,
        ).digest()
        return _b64encode(digest)
