from pathlib import Path

from jinguzhou.config import load_runtime_config
from jinguzhou.gateway.runtime import build_app_from_config
from jinguzhou.providers.openai_compatible import OpenAICompatibleProvider


def test_runtime_config_resolves_api_key_from_env(tmp_path: Path) -> None:
    config_path = tmp_path / "jinguzhou.yaml"
    config_path.write_text(
        "\n".join(
            [
                "gateway:",
                "  host: 0.0.0.0",
                "  port: 9999",
                "policy:",
                "  files:",
                "    - rules/baseline.yaml",
                "provider:",
                "  type: openai-compatible",
                "  base_url: https://api.openai.com",
                "  api_key_env: TEST_OPENAI_KEY",
                "  timeout_seconds: 12.5",
                "  headers:",
                "    X-Test-Header: config-value",
                "audit:",
                "  enabled: true",
                "  path: .jinguzhou/audit.jsonl",
                "approvals:",
                "  enabled: true",
                "  secret_env: TEST_APPROVAL_SECRET",
                "  ttl_seconds: 120",
            ]
        ),
        encoding="utf-8",
    )

    config = load_runtime_config(
        config_path,
        env={"TEST_OPENAI_KEY": "secret-key", "TEST_APPROVAL_SECRET": "approval-secret"},
    )

    assert config.gateway.host == "0.0.0.0"
    assert config.gateway.port == 9999
    assert config.provider.api_key == "secret-key"
    assert config.provider.timeout_seconds == 12.5
    assert config.provider.headers["X-Test-Header"] == "config-value"
    assert config.approvals.secret == "approval-secret"
    assert config.approvals.ttl_seconds == 120
    assert config.tool_adapters == []


def test_build_app_from_config_wires_provider_policy_and_audit(tmp_path: Path) -> None:
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "baseline.yaml").write_text(
        "\n".join(
            [
                "version: 1",
                "name: local-baseline",
                "rules:",
                "  - id: local.warn",
                "    stage: input",
                "    category: test",
                "    severity: medium",
                "    action: warn",
                "    reason: local test rule",
                "    match:",
                "      any_keywords:",
                "        - hello",
            ]
        ),
        encoding="utf-8",
    )
    config_path = tmp_path / "jinguzhou.yaml"
    config_path.write_text(
        "\n".join(
            [
                "policy:",
                "  files:",
                "    - rules/baseline.yaml",
                "provider:",
                "  type: openai-compatible",
                "  base_url: https://api.openai.com",
                "  api_key: direct-key",
                "  timeout_seconds: 33",
                "  headers:",
                "    X-From-Config: yes",
                "audit:",
                "  enabled: true",
                "  path: audit/events.jsonl",
            ]
        ),
        encoding="utf-8",
    )

    config = load_runtime_config(config_path)
    app = build_app_from_config(config, tmp_path)

    assert app.state.policy_engine is not None
    assert app.state.policy_engine.policy.name == "local-baseline"
    assert isinstance(app.state.provider, OpenAICompatibleProvider)
    assert app.state.provider.base_url == "https://api.openai.com"
    assert app.state.provider.api_key == "direct-key"
    assert app.state.provider.timeout_seconds == 33
    assert app.state.provider.default_headers["X-From-Config"] == "true"
    assert app.state.audit_logger is not None
    assert app.state.audit_logger.path == tmp_path / "audit/events.jsonl"
    assert app.state.tool_adapter_registry is not None


def test_build_app_from_config_loads_custom_tool_adapters(tmp_path: Path) -> None:
    config_path = tmp_path / "jinguzhou.yaml"
    config_path.write_text(
        "\n".join(
            [
                "provider:",
                "  type: openai-compatible",
                "  base_url: https://api.openai.com",
                "tool_adapters:",
                "  - name: custom-db-adapter",
                "    protocols:",
                "      - langchain",
                "    tool_name_patterns:",
                "      - custom.db.*",
                "    priority: 250",
                "    extraction:",
                "      sql_fields:",
                "        - statement_text",
            ]
        ),
        encoding="utf-8",
    )

    config = load_runtime_config(config_path)
    app = build_app_from_config(config, tmp_path)
    adapter = app.state.tool_adapter_registry.resolve("langchain", "custom.db.run")

    assert adapter.name == "custom-db-adapter"
    assert adapter.extraction.sql_fields == ["statement_text"]
