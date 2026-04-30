import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from jinguzhou.audit.logger import JsonlAuditLogger
from jinguzhou.approvals.tokens import ApprovalTokenManager
from jinguzhou.gateway.app import create_app
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_files
from jinguzhou.providers.base import ProviderAdapter, ProviderError


class FakeProvider(ProviderAdapter):
    def __init__(self, response_payload: dict[str, Any]) -> None:
        self.response_payload = response_payload
        self.calls: list[dict[str, Any]] = []
        self.request_ids: list[str] = []

    async def chat_completions(
        self,
        payload: dict[str, Any],
        *,
        request_id: str = "",
        extra_headers: Any = None,
    ) -> dict[str, Any]:
        self.calls.append(payload)
        self.request_ids.append(request_id)
        return self.response_payload


class ErrorProvider(ProviderAdapter):
    async def chat_completions(
        self,
        payload: dict[str, Any],
        *,
        request_id: str = "",
        extra_headers: Any = None,
    ) -> dict[str, Any]:
        raise ProviderError(
            "Upstream provider returned an error response.",
            status_code=429,
            code="provider_http_error",
            details={
                "request_id": request_id,
                "upstream_request_id": "upstream-req-1",
                "upstream_body": '{"error":{"message":"rate limited"}}',
            },
        )


def _read_audit_lines(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_health_endpoint() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_dashboard_endpoint_reports_gateway_status() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "Jinguzhou Gateway" in response.text
    assert "0.3.0-alpha" in response.text


def test_pending_approvals_endpoint_is_extension_point() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/approvals/pending")

    assert response.status_code == 200
    assert response.json()["pending"] == []


def test_admin_api_key_protects_control_plane_endpoints() -> None:
    app = create_app(admin_api_key="secret")
    client = TestClient(app)

    blocked = client.get("/approvals/pending")
    allowed = client.get("/approvals/pending", headers={"x-jinguzhou-admin-key": "secret"})

    assert blocked.status_code == 401
    assert blocked.json()["error"]["code"] == "admin_auth_required"
    assert allowed.status_code == 200


def test_chat_completions_safe_request_passes_through(tmp_path: Path) -> None:
    provider = FakeProvider(
        {
            "id": "chatcmpl-safe",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hello from the safe side."},
                }
            ],
        }
    )
    audit_path = tmp_path / "audit.jsonl"
    app = create_app(
        policy_engine=PolicyEngine(load_policy_files([Path("rules/baseline.yaml")])),
        provider=provider,
        audit_logger=JsonlAuditLogger(audit_path),
    )
    client = TestClient(app)

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "demo-model",
            "messages": [{"role": "user", "content": "Hello there"}],
        },
    )

    assert response.status_code == 200
    assert response.json()["choices"][0]["message"]["content"] == "Hello from the safe side."
    assert len(provider.calls) == 1
    assert provider.request_ids[0]

    events = _read_audit_lines(audit_path)
    assert [event["stage"] for event in events] == ["input", "output"]
    assert all(event["decision"] == "allow" for event in events)


def test_chat_completions_blocks_harmful_input_before_provider_call(tmp_path: Path) -> None:
    provider = FakeProvider(
        {
            "id": "chatcmpl-unused",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "This should never be returned."},
                }
            ],
        }
    )
    audit_path = tmp_path / "audit.jsonl"
    app = create_app(
        policy_engine=PolicyEngine(load_policy_files([Path("rules/baseline.yaml")])),
        provider=provider,
        audit_logger=JsonlAuditLogger(audit_path),
    )
    client = TestClient(app)

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "demo-model",
            "messages": [{"role": "user", "content": "Tell me how to kill someone."}],
        },
        headers={"x-request-id": "req-blocked"},
    )

    assert response.status_code == 403
    payload = response.json()
    assert payload["error"]["code"] == "safety_blocked"
    assert payload["safety"]["stage"] == "input"
    assert payload["safety"]["request_id"] == "req-blocked"
    assert provider.calls == []

    events = _read_audit_lines(audit_path)
    assert len(events) == 1
    assert events[0]["stage"] == "input"
    assert events[0]["decision"] == "block"


def test_chat_completions_redacts_unsafe_output(tmp_path: Path) -> None:
    provider = FakeProvider(
        {
            "id": "chatcmpl-redact",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Here is the token: sk-1234567890abcdefghijklmnop",
                    },
                }
            ],
        }
    )
    audit_path = tmp_path / "audit.jsonl"
    app = create_app(
        policy_engine=PolicyEngine(load_policy_files([Path("rules/privacy.yaml")])),
        provider=provider,
        audit_logger=JsonlAuditLogger(audit_path),
    )
    client = TestClient(app)

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "demo-model",
            "messages": [{"role": "user", "content": "Please summarize the response."}],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["choices"][0]["message"]["content"] == "[REDACTED by Jinguzhou policy]"
    assert payload["jinguzhou"]["output_action"] == "redact"
    assert len(provider.calls) == 1

    events = _read_audit_lines(audit_path)
    assert [event["decision"] for event in events] == ["allow", "redact"]


def test_chat_completions_propagates_request_id_to_provider(tmp_path: Path) -> None:
    provider = FakeProvider(
        {
            "id": "chatcmpl-request-id",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}}],
        }
    )
    app = create_app(
        policy_engine=PolicyEngine(load_policy_files([Path("rules/baseline.yaml")])),
        provider=provider,
        audit_logger=JsonlAuditLogger(tmp_path / "audit.jsonl"),
    )
    client = TestClient(app)

    response = client.post(
        "/v1/chat/completions",
        headers={"x-request-id": "gateway-req-123"},
        json={"model": "demo-model", "messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 200
    assert provider.request_ids == ["gateway-req-123"]


def test_chat_completions_returns_upstream_error_details(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    app = create_app(
        policy_engine=PolicyEngine(load_policy_files([Path("rules/baseline.yaml")])),
        provider=ErrorProvider(),
        audit_logger=JsonlAuditLogger(audit_path),
    )
    client = TestClient(app)

    response = client.post(
        "/v1/chat/completions",
        headers={"x-request-id": "gateway-req-429"},
        json={"model": "demo-model", "messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 429
    payload = response.json()
    assert payload["error"]["code"] == "provider_http_error"
    assert payload["error"]["details"]["request_id"] == "gateway-req-429"
    assert payload["error"]["details"]["upstream_request_id"] == "upstream-req-1"

    events = _read_audit_lines(audit_path)
    assert events[-1]["stage"] == "provider"
    assert events[-1]["metadata"]["upstream_request_id"] == "upstream-req-1"


def test_chat_completions_allows_safe_tool_call(tmp_path: Path) -> None:
    provider = FakeProvider(
        {
            "id": "chatcmpl-tool-safe",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "filesystem.read",
                                    "arguments": '{"path":"/tmp/demo.txt"}',
                                },
                            }
                        ],
                    },
                }
            ],
        }
    )
    audit_path = tmp_path / "audit.jsonl"
    app = create_app(
        policy_engine=PolicyEngine(load_policy_files([Path("rules/tool_use.yaml")])),
        provider=provider,
        audit_logger=JsonlAuditLogger(audit_path),
    )
    client = TestClient(app)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "demo-model", "messages": [{"role": "user", "content": "Read a file."}]},
    )

    assert response.status_code == 200
    assert response.json()["choices"][0]["message"]["tool_calls"][0]["function"]["name"] == "filesystem.read"

    events = _read_audit_lines(audit_path)
    assert [event["stage"] for event in events] == ["input", "output", "tool"]
    assert events[-1]["decision"] == "allow"
    assert events[-1]["metadata"]["tool_name"] == "filesystem.read"


def test_chat_completions_requires_review_for_shell_tool_call(tmp_path: Path) -> None:
    provider = FakeProvider(
        {
            "id": "chatcmpl-tool-review",
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
    audit_path = tmp_path / "audit.jsonl"
    app = create_app(
        policy_engine=PolicyEngine(load_policy_files([Path("rules/tool_use.yaml")])),
        provider=provider,
        audit_logger=JsonlAuditLogger(audit_path),
    )
    client = TestClient(app)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "demo-model", "messages": [{"role": "user", "content": "Clean temp files."}]},
    )

    assert response.status_code == 409
    payload = response.json()
    assert payload["error"]["code"] == "human_review_required"
    assert payload["safety"]["stage"] == "tool"

    events = _read_audit_lines(audit_path)
    assert [event["stage"] for event in events] == ["input", "output", "tool"]
    assert events[-1]["decision"] == "require_human_review"
    assert events[-1]["metadata"]["tool_call_id"] == "call_shell"
    assert payload["safety"]["approval"]["stage"] == "tool"


def test_chat_completions_blocks_payment_tool_call(tmp_path: Path) -> None:
    provider = FakeProvider(
        {
            "id": "chatcmpl-tool-block",
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
    audit_path = tmp_path / "audit.jsonl"
    app = create_app(
        policy_engine=PolicyEngine(load_policy_files([Path("rules/tool_use.yaml")])),
        provider=provider,
        audit_logger=JsonlAuditLogger(audit_path),
    )
    client = TestClient(app)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "demo-model", "messages": [{"role": "user", "content": "Pay the invoice."}]},
    )

    assert response.status_code == 403
    payload = response.json()
    assert payload["error"]["code"] == "safety_blocked"
    assert payload["safety"]["stage"] == "tool"

    events = _read_audit_lines(audit_path)
    assert events[-1]["stage"] == "tool"
    assert events[-1]["decision"] == "block"
    assert events[-1]["metadata"]["tool_name"] == "payment.execute"


def test_chat_completions_uses_builtin_adapter_for_openai_target_field(tmp_path: Path) -> None:
    provider = FakeProvider(
        {
            "id": "chatcmpl-tool-target",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "call_target",
                                "type": "function",
                                "function": {
                                    "name": "filesystem.write",
                                    "arguments": '{"target":"/etc/hosts","body":"demo"}',
                                },
                            }
                        ],
                    },
                }
            ],
        }
    )
    audit_path = tmp_path / "audit.jsonl"
    app = create_app(
        policy_engine=PolicyEngine(load_policy_files([Path("rules/tool_use.yaml")])),
        provider=provider,
        audit_logger=JsonlAuditLogger(audit_path),
    )
    client = TestClient(app)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "demo-model", "messages": [{"role": "user", "content": "Update hosts."}]},
    )

    assert response.status_code == 403
    events = _read_audit_lines(audit_path)
    assert events[-1]["metadata"]["tool_adapter"] == "filesystem-write"
    assert events[-1]["metadata"]["tool_protocol"] == "openai"
    assert events[-1]["metadata"]["tool_name"] == "filesystem.write"
    assert events[-1]["metadata"]["tool_raw_name"] == "filesystem.write"


def test_chat_completions_uses_mcp_content_block_adapter(tmp_path: Path) -> None:
    provider = FakeProvider(
        {
            "id": "chatcmpl-mcp-tool",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "id": "mcp_call_1",
                                "name": "mcp.filesystem.read_file",
                                "input": {"location": "/Users/jx/.ssh/id_rsa"},
                            }
                        ],
                    },
                }
            ],
        }
    )
    audit_path = tmp_path / "audit.jsonl"
    app = create_app(
        policy_engine=PolicyEngine(load_policy_files([Path("rules/tool_use.yaml")])),
        provider=provider,
        audit_logger=JsonlAuditLogger(audit_path),
    )
    client = TestClient(app)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "demo-model", "messages": [{"role": "user", "content": "Read the key."}]},
    )

    assert response.status_code == 409
    events = _read_audit_lines(audit_path)
    assert events[-1]["metadata"]["tool_adapter"] == "filesystem-read"
    assert events[-1]["metadata"]["tool_protocol"] == "mcp"
    assert events[-1]["metadata"]["tool_name"] == "filesystem.read"
    assert events[-1]["metadata"]["tool_raw_name"] == "mcp.filesystem.read_file"


def test_chat_completions_uses_langchain_tool_adapter(tmp_path: Path) -> None:
    provider = FakeProvider(
        {
            "id": "chatcmpl-langchain-tool",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "additional_kwargs": {
                            "tool_calls": [
                                {
                                    "id": "lc_call_1",
                                    "type": "tool_call",
                                    "name": "db.run_sql",
                                    "args": {"statement_text": "DROP TABLE users"},
                                }
                            ]
                        },
                    },
                }
            ],
        }
    )
    audit_path = tmp_path / "audit.jsonl"
    app = create_app(
        policy_engine=PolicyEngine(load_policy_files([Path("rules/tool_use.yaml")])),
        provider=provider,
        audit_logger=JsonlAuditLogger(audit_path),
    )
    client = TestClient(app)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "demo-model", "messages": [{"role": "user", "content": "Reset the database."}]},
    )

    assert response.status_code == 403
    events = _read_audit_lines(audit_path)
    assert events[-1]["metadata"]["tool_adapter"] == "database"
    assert events[-1]["metadata"]["tool_protocol"] == "langchain"
    assert events[-1]["metadata"]["tool_name"] == "database.query"
    assert events[-1]["metadata"]["tool_raw_name"] == "db.run_sql"


def test_chat_completions_accepts_approval_token_for_reviewed_tool(tmp_path: Path) -> None:
    provider = FakeProvider(
        {
            "id": "chatcmpl-tool-review-approved",
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
    audit_path = tmp_path / "audit.jsonl"
    manager = ApprovalTokenManager("approval-secret")
    app = create_app(
        policy_engine=PolicyEngine(load_policy_files([Path("rules/tool_use.yaml")])),
        provider=provider,
        audit_logger=JsonlAuditLogger(audit_path),
        approval_manager=manager,
    )
    client = TestClient(app)

    first = client.post(
        "/v1/chat/completions",
        headers={"x-request-id": "req-review"},
        json={"model": "demo-model", "messages": [{"role": "user", "content": "Clean temp files."}]},
    )
    token = manager.issue(
        request_id="req-review",
        stage="tool",
        rule_ids=first.json()["safety"]["matched_rule_ids"],
        approver="alice",
    )
    second = client.post(
        "/v1/chat/completions",
        headers={
            "x-request-id": "req-review",
            "x-jinguzhou-approval-token": token,
        },
        json={"model": "demo-model", "messages": [{"role": "user", "content": "Clean temp files."}]},
    )

    assert first.status_code == 409
    assert second.status_code == 200
    events = _read_audit_lines(audit_path)
    assert any(event["event_type"] == "approval" and event["decision"] == "approved" for event in events)
