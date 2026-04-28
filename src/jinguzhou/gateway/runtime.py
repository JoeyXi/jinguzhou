"""Helpers for building a configured gateway application."""

from __future__ import annotations

from pathlib import Path

from jinguzhou.audit.logger import JsonlAuditLogger
from jinguzhou.audit.postgres import PostgresAuditLogger
from jinguzhou.approvals.tokens import ApprovalTokenManager
from jinguzhou.config import RuntimeConfig
from jinguzhou.gateway.app import create_app
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_files
from jinguzhou.providers.openai_compatible import OpenAICompatibleProvider
from jinguzhou.tools.adapters import ToolAdapterRegistry


def build_app_from_config(config: RuntimeConfig, config_dir: Path):
    """Build a configured FastAPI app from runtime settings."""
    policy_engine = None
    if config.policy.files:
        policy_paths = [config_dir / relative_path for relative_path in config.policy.files]
        policy_engine = PolicyEngine(load_policy_files(policy_paths))

    audit_logger = None
    if config.audit.enabled:
        if config.audit.backend == "jsonl":
            audit_logger = JsonlAuditLogger(config_dir / config.audit.path, redact=config.audit.redact)
        elif config.audit.backend == "postgres":
            audit_logger = PostgresAuditLogger(
                config.audit.postgres_dsn,
                table=config.audit.postgres_table,
                redact=config.audit.redact,
            )
        else:
            raise ValueError(f"Unsupported audit backend: {config.audit.backend}")

    approval_manager = None
    if config.approvals.enabled and config.approvals.secret:
        approval_manager = ApprovalTokenManager(config.approvals.secret)

    provider = None
    if config.provider.type == "openai-compatible":
        provider = OpenAICompatibleProvider(
            base_url=config.provider.base_url,
            api_key=config.provider.api_key,
            timeout_seconds=config.provider.timeout_seconds,
            default_headers=config.provider.headers,
        )
    elif config.provider.type:
        raise ValueError(f"Unsupported provider type: {config.provider.type}")

    tool_adapter_registry = ToolAdapterRegistry.with_defaults(config.tool_adapters)

    return create_app(
        policy_engine=policy_engine,
        provider=provider,
        audit_logger=audit_logger,
        tool_adapter_registry=tool_adapter_registry,
        approval_manager=approval_manager,
        admin_api_key=config.security.admin_api_key,
    )
