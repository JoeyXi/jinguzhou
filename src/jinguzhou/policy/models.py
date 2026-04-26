"""Pydantic models for policy data and evaluation results."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

Stage = Literal["input", "output", "tool"]
Action = Literal["allow", "warn", "block", "redact", "require_human_review"]
Severity = Literal["low", "medium", "high", "critical"]


class MatchConfig(BaseModel):
    """Supported rule match operations for the MVP and richer tool policy checks."""

    any_keywords: list[str] = Field(default_factory=list)
    all_keywords: list[str] = Field(default_factory=list)
    regex: list[str] = Field(default_factory=list)
    tool_name: Optional[str] = None
    command_contains: list[str] = Field(default_factory=list)
    path_starts_with: list[str] = Field(default_factory=list)
    path_regex: list[str] = Field(default_factory=list)
    path_sensitivity_in: list[str] = Field(default_factory=list)
    domain_in: list[str] = Field(default_factory=list)
    domain_suffix_in: list[str] = Field(default_factory=list)
    db_operation_in: list[str] = Field(default_factory=list)
    metadata_equals: dict[str, str] = Field(default_factory=dict)
    model_in: list[str] = Field(default_factory=list)
    provider_in: list[str] = Field(default_factory=list)


class ToolExtractionConfig(BaseModel):
    """Configurable field mapping for extracting normalized tool facts."""

    command_fields: list[str] = Field(
        default_factory=lambda: ["command", "cmd", "cmdline", "shell_command"]
    )
    path_fields: list[str] = Field(
        default_factory=lambda: [
            "path",
            "paths",
            "filepath",
            "file_path",
            "target_path",
            "source_path",
            "destination_path",
            "directory",
            "dir",
            "cwd",
            "root",
            "filename",
        ]
    )
    path_sensitivity_fields: list[str] = Field(
        default_factory=lambda: ["path_sensitivity", "sensitivity", "data_classification"]
    )
    url_fields: list[str] = Field(
        default_factory=lambda: [
            "url",
            "uri",
            "endpoint",
            "base_url",
            "webhook_url",
            "host",
            "hostname",
            "domain",
        ]
    )
    db_operation_fields: list[str] = Field(
        default_factory=lambda: ["operation", "op", "query_type", "method", "action"]
    )
    sql_fields: list[str] = Field(default_factory=lambda: ["sql", "query", "statement"])


class ToolFacts(BaseModel):
    """Normalized structured facts extracted from a tool payload."""

    commands: list[str] = Field(default_factory=list)
    paths: list[str] = Field(default_factory=list)
    path_sensitivities: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    db_operations: list[str] = Field(default_factory=list)


class Rule(BaseModel):
    """A single policy rule."""

    id: str
    stage: Stage
    category: str
    severity: Severity
    action: Action
    reason: str
    priority: int = 0
    match: MatchConfig = Field(default_factory=MatchConfig)


class PolicyDocument(BaseModel):
    """Top-level policy document."""

    version: int = 1
    name: str
    description: str = ""
    sources: list[str] = Field(default_factory=list)
    rules: list[Rule] = Field(default_factory=list)


class EvaluationContext(BaseModel):
    """Normalized context evaluated by the policy engine."""

    stage: Stage
    text: str = ""
    model: str = ""
    provider: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)
    tool_name: str = ""
    tool_payload: Any = Field(default_factory=dict)
    tool_extraction: ToolExtractionConfig = Field(default_factory=ToolExtractionConfig)


class RuleMatch(BaseModel):
    """Details about a matched rule."""

    rule_id: str
    action: Action
    category: str
    severity: Severity
    reason: str
    priority: int = 0


class EvaluationResult(BaseModel):
    """Final policy decision."""

    action: Action
    matched_rules: list[RuleMatch] = Field(default_factory=list)
    policy_name: str
    summary: str
