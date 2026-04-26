"""Configurable extraction of normalized facts from tool payloads."""

from __future__ import annotations

import os
import re
from typing import Any, Iterable
from urllib.parse import urlparse

from jinguzhou.policy.models import EvaluationContext, ToolExtractionConfig, ToolFacts

SQL_KEYWORDS = {
    "select",
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "truncate",
    "grant",
    "revoke",
}


def flatten_strings(value: Any) -> list[str]:
    """Recursively flatten a nested value into a list of strings."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (int, float)):
        return [str(value)]
    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(flatten_strings(item))
        return result
    if isinstance(value, dict):
        result = []
        for item in value.values():
            result.extend(flatten_strings(item))
        return result
    return []


def _looks_like_path_expression(field_name: str) -> bool:
    return field_name.startswith("$") or "." in field_name or "[" in field_name


def _tokenize_path_expression(expression: str) -> list[str]:
    cleaned = expression.strip()
    if cleaned.startswith("$."):
        cleaned = cleaned[2:]
    elif cleaned.startswith("$"):
        cleaned = cleaned[1:]
    return [token for token in re.split(r"\.", cleaned) if token]


def _resolve_path_token(value: Any, token: str) -> list[Any]:
    list_match = re.fullmatch(r"([^\[]+)\[(\*|\d+)\]", token)
    if list_match:
        key, selector = list_match.groups()
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return []
        if not isinstance(value, list):
            return []
        if selector == "*":
            return list(value)
        index = int(selector)
        return [value[index]] if 0 <= index < len(value) else []

    if token in {"*", "[*]"}:
        if isinstance(value, list):
            return list(value)
        if isinstance(value, dict):
            return list(value.values())
        return []

    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() == token.lower():
                return [item]
    return []


def resolve_field_path(payload: Any, expression: str) -> list[Any]:
    """Resolve a small JSONPath-like expression against a payload."""
    values = [payload]
    for token in _tokenize_path_expression(expression):
        next_values = []
        for value in values:
            next_values.extend(_resolve_path_token(value, token))
        values = next_values
        if not values:
            break
    return values


def extract_candidate_values(payload: Any, field_names: Iterable[str]) -> list[str]:
    """Extract string values from top-level fields or JSONPath-like expressions."""
    if not isinstance(payload, dict):
        return []

    expected = {name.lower() for name in field_names}
    values = []
    for field_name in field_names:
        if _looks_like_path_expression(field_name):
            for value in resolve_field_path(payload, field_name):
                values.extend(flatten_strings(value))
    for key, value in payload.items():
        if str(key).lower() in expected:
            values.extend(flatten_strings(value))
    return values


def normalize_path(path: str) -> str:
    """Normalize a filesystem-like path for matching."""
    return os.path.normpath(path).replace("\\", "/").lower()


def classify_path_sensitivity(path: str) -> str:
    """Classify a path into a coarse safety-relevant sensitivity bucket."""
    normalized = normalize_path(path)

    if normalized.startswith(("/etc", "/bin", "/sbin", "/usr", "/var", "/opt", "/system", "c:/windows")):
        return "system"
    if any(
        token in normalized
        for token in [".ssh", ".aws", ".env", "/secrets", "id_rsa", "credentials", ".npmrc", ".pypirc"]
    ):
        return "secrets"
    if normalized.startswith(("/users/", "/home/")) or any(
        segment in normalized for segment in ["/desktop", "/documents", "/downloads", "/pictures", "/library/"]
    ):
        return "user_data"
    if not normalized.startswith("/"):
        return "workspace"
    return "unknown"


def extract_tool_facts(context: EvaluationContext) -> ToolFacts:
    """Extract normalized facts from a tool payload using configurable field mappings."""
    payload = context.tool_payload
    config: ToolExtractionConfig = context.tool_extraction

    commands = extract_candidate_values(payload, config.command_fields)
    paths = [path for path in extract_candidate_values(payload, config.path_fields) if path]

    explicit_sensitivities = [
        value.lower() for value in extract_candidate_values(payload, config.path_sensitivity_fields) if value
    ]
    path_sensitivities = explicit_sensitivities or [classify_path_sensitivity(path) for path in paths]

    domains = []
    for value in extract_candidate_values(payload, config.url_fields):
        parsed = urlparse(value if "://" in value else f"https://{value}")
        host = parsed.hostname or parsed.path
        if host:
            domains.append(host.lower())

    db_operations = {value.lower() for value in extract_candidate_values(payload, config.db_operation_fields)}
    for sql in extract_candidate_values(payload, config.sql_fields):
        keyword = sql.strip().split(maxsplit=1)[0].lower() if sql.strip() else ""
        if keyword in SQL_KEYWORDS:
            db_operations.add(keyword)

    return ToolFacts(
        commands=commands,
        paths=paths,
        path_sensitivities=sorted(set(path_sensitivities)),
        domains=sorted(set(domains)),
        db_operations=sorted(db_operations),
    )
