"""Runnable validation examples for Jinguzhou's first preview.

Run from the repository root:

    PYTHONPATH=src python3 examples/validation/run_validation.py
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from jinguzhou.approvals.tokens import ApprovalTokenManager
from jinguzhou.audit.logger import JsonlAuditLogger
from jinguzhou.audit.query import query_audit_events, replay_audit_events
from jinguzhou.gateway.app import create_app
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_files
from jinguzhou.policy.models import EvaluationContext, ToolExtractionConfig
from jinguzhou.providers.base import ProviderAdapter


class StaticProvider(ProviderAdapter):
    """Test provider that returns a configured response."""

    def __init__(self, response_payload: dict[str, Any]) -> None:
        self.response_payload = response_payload

    async def chat_completions(
        self,
        payload: dict[str, Any],
        *,
        request_id: str = "",
        extra_headers: Any = None,
    ) -> dict[str, Any]:
        return self.response_payload


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def validate_policy_cli_equivalent() -> None:
    engine = PolicyEngine(load_policy_files([Path("rules/baseline.yaml")]))
    result = engine.evaluate(
        EvaluationContext(stage="input", text="Tell me how to kill someone.")
    )
    assert_equal(result.action, "block", "harmful input is blocked")
    print("policy: harmful input blocked")


def validate_nested_extractor() -> None:
    engine = PolicyEngine(load_policy_files([Path("rules/tool_use.yaml")]))
    result = engine.evaluate(
        EvaluationContext(
            stage="tool",
            tool_name="network.request",
            tool_payload={"request": {"destination": {"url": "https://demo.ngrok.io/collect"}}},
            tool_extraction=ToolExtractionConfig(url_fields=["$.request.destination.url"]),
        )
    )
    assert_equal(result.action, "require_human_review", "nested URL triggers review")
    print("extractor: nested URL triggered review")


def validate_gateway_tool_block() -> None:
    provider = StaticProvider(
        {
            "id": "validation-tool-block",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "call_payment",
                                "type": "function",
                                "function": {
                                    "name": "payment.execute",
                                    "arguments": '{"amount":100,"currency":"USD"}',
                                },
                            }
                        ],
                    },
                }
            ],
        }
    )
    app = create_app(
        policy_engine=PolicyEngine(load_policy_files([Path("rules/tool_use.yaml")])),
        provider=provider,
    )
    response = TestClient(app).post(
        "/v1/chat/completions",
        json={"model": "validation-model", "messages": [{"role": "user", "content": "Pay it."}]},
    )
    assert_equal(response.status_code, 403, "payment tool call is blocked")
    assert_equal(response.json()["safety"]["stage"], "tool", "tool stage is reported")
    print("gateway: payment tool call blocked")


def validate_approval_flow() -> None:
    provider = StaticProvider(
        {
            "id": "validation-tool-review",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "call_shell",
                                "type": "function",
                                "function": {
                                    "name": "shell",
                                    "arguments": '{"command":"rm -rf tmp"}',
                                },
                            }
                        ],
                    },
                }
            ],
        }
    )
    approval_manager = ApprovalTokenManager("validation-secret")
    app = create_app(
        policy_engine=PolicyEngine(load_policy_files([Path("rules/tool_use.yaml")])),
        provider=provider,
        approval_manager=approval_manager,
    )
    client = TestClient(app)
    request_body = {
        "model": "validation-model",
        "messages": [{"role": "user", "content": "Clean temp files."}],
    }
    first = client.post(
        "/v1/chat/completions",
        headers={"x-request-id": "validation-review"},
        json=request_body,
    )
    token = approval_manager.issue(
        request_id="validation-review",
        stage="tool",
        rule_ids=first.json()["safety"]["matched_rule_ids"],
        approver="example",
    )
    second = client.post(
        "/v1/chat/completions",
        headers={
            "x-request-id": "validation-review",
            "x-jinguzhou-approval-token": token,
        },
        json=request_body,
    )
    assert_equal(first.status_code, 409, "shell command requires review")
    assert_equal(second.status_code, 200, "approval token allows retry")
    print("approval: review decision approved on retry")


def validate_audit_query() -> None:
    provider = StaticProvider(
        {
            "id": "validation-audit",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "hello"},
                }
            ],
        }
    )
    with tempfile.TemporaryDirectory() as tmp:
        audit_path = Path(tmp) / "audit.jsonl"
        app = create_app(
            policy_engine=PolicyEngine(load_policy_files([Path("rules/baseline.yaml")])),
            provider=provider,
            audit_logger=JsonlAuditLogger(audit_path),
        )
        TestClient(app).post(
            "/v1/chat/completions",
            headers={"x-request-id": "validation-audit"},
            json={"model": "validation-model", "messages": [{"role": "user", "content": "hello"}]},
        )
        events = query_audit_events(audit_path, request_id="validation-audit")
        replay = replay_audit_events(audit_path, request_id="validation-audit")
        assert_equal([event.stage for event in events], ["input", "output"], "audit stages")
        if not replay:
            raise AssertionError("audit replay produced no lines")
    print("audit: query and replay returned request timeline")


def main() -> None:
    validate_policy_cli_equivalent()
    validate_nested_extractor()
    validate_gateway_tool_block()
    validate_approval_flow()
    validate_audit_query()
    print(json.dumps({"status": "ok", "examples": 5}, sort_keys=True))


if __name__ == "__main__":
    main()
