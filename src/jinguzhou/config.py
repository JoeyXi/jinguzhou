"""Runtime configuration models and loaders for Jinguzhou."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping, Optional

import yaml
from pydantic import BaseModel, Field, field_validator
from jinguzhou.tools.adapters import ToolAdapterConfig


class GatewaySettings(BaseModel):
    """HTTP listener settings for the gateway."""

    host: str = "127.0.0.1"
    port: int = 8787


class PolicySettings(BaseModel):
    """Policy configuration for runtime enforcement."""

    files: list[str] = Field(default_factory=list)


class ProviderSettings(BaseModel):
    """Provider configuration for upstream model access."""

    type: str = "openai-compatible"
    base_url: str = ""
    api_key: str = ""
    api_key_env: str = "OPENAI_API_KEY"
    timeout_seconds: float = 60.0
    headers: dict[str, str] = Field(default_factory=dict)

    @field_validator("headers", mode="before")
    @classmethod
    def normalize_headers(cls, value: object) -> dict[str, str]:
        """Convert YAML-loaded header values into strings."""
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise TypeError("provider.headers must be a mapping.")
        normalized = {}
        for key, item in value.items():
            if isinstance(item, bool):
                normalized[str(key)] = "true" if item else "false"
            else:
                normalized[str(key)] = str(item)
        return normalized


class AuditSettings(BaseModel):
    """Audit logging configuration."""

    enabled: bool = True
    path: str = ".jinguzhou/audit.jsonl"
    redact: bool = True


class ApprovalSettings(BaseModel):
    """Approval token configuration."""

    enabled: bool = True
    secret: str = ""
    secret_env: str = "JINGUZHOU_APPROVAL_SECRET"
    ttl_seconds: int = 900


class RuntimeConfig(BaseModel):
    """Top-level runtime configuration."""

    gateway: GatewaySettings = Field(default_factory=GatewaySettings)
    policy: PolicySettings = Field(default_factory=PolicySettings)
    provider: ProviderSettings = Field(default_factory=ProviderSettings)
    audit: AuditSettings = Field(default_factory=AuditSettings)
    approvals: ApprovalSettings = Field(default_factory=ApprovalSettings)
    tool_adapters: list[ToolAdapterConfig] = Field(default_factory=list)


def load_runtime_config(
    path: Path,
    env: Optional[Mapping[str, str]] = None,
) -> RuntimeConfig:
    """Load runtime configuration from YAML and resolve env-backed values."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    config = RuntimeConfig.model_validate(raw)
    env_map = env if env is not None else os.environ

    if not config.provider.api_key and config.provider.api_key_env:
        config.provider.api_key = env_map.get(config.provider.api_key_env, "")
    if not config.approvals.secret and config.approvals.secret_env:
        config.approvals.secret = env_map.get(config.approvals.secret_env, "")

    return config
