"""Configurable extraction of normalized facts from tool payloads."""

from __future__ import annotations

import os
import re
from typing import Any, Iterable, Union
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

PathToken = tuple[str, Union[str, int, None]]


class FieldPathError(ValueError):
    """Raised when a configured extractor path cannot be parsed."""


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


def _read_path_key(expression: str, start: int) -> tuple[str, int]:
    end = start
    while end < len(expression) and expression[end] not in ".[":
        end += 1
    key = expression[start:end].strip()
    if not key:
        raise FieldPathError(f"Invalid field path expression: {expression}")
    return key, end


def _read_bracket_token(expression: str, start: int) -> tuple[PathToken, int]:
    end = start + 1
    quote = ""
    while end < len(expression):
        char = expression[end]
        if quote:
            if char == quote:
                quote = ""
        elif char in {"'", '"'}:
            quote = char
        elif char == "]":
            break
        end += 1

    if end >= len(expression) or expression[end] != "]":
        raise FieldPathError(f"Unclosed bracket in field path expression: {expression}")

    raw_content = expression[start + 1 : end].strip()
    if raw_content == "*":
        return ("wildcard", None), end + 1
    if re.fullmatch(r"-?\d+", raw_content):
        return ("index", int(raw_content)), end + 1
    if (
        len(raw_content) >= 2
        and raw_content[0] == raw_content[-1]
        and raw_content[0] in {"'", '"'}
    ):
        return ("key", raw_content[1:-1]), end + 1
    if raw_content:
        return ("key", raw_content), end + 1
    raise FieldPathError(f"Empty bracket in field path expression: {expression}")


def _tokenize_path_expression(expression: str) -> list[PathToken]:
    cleaned = expression.strip()
    if not cleaned:
        return []
    if cleaned.startswith("$"):
        index = 1
    else:
        index = 0

    tokens: list[PathToken] = []
    while index < len(cleaned):
        if cleaned.startswith("..", index):
            key, index = _read_path_key(cleaned, index + 2)
            if key == "*":
                tokens.append(("recursive_wildcard", None))
            else:
                tokens.append(("recursive_key", key))
            continue
        char = cleaned[index]
        if char == ".":
            key, index = _read_path_key(cleaned, index + 1)
            if key == "*":
                tokens.append(("wildcard", None))
            else:
                tokens.append(("key", key))
            continue
        if char == "[":
            token, index = _read_bracket_token(cleaned, index)
            tokens.append(token)
            continue
        key, index = _read_path_key(cleaned, index)
        tokens.append(("key", key))
    return tokens


def _match_dict_key(value: dict[Any, Any], key: str) -> list[Any]:
    for candidate, item in value.items():
        if str(candidate).lower() == key.lower():
            return [item]
    return []


def _recursive_find_key(value: Any, key: str) -> list[Any]:
    matches: list[Any] = []
    if isinstance(value, dict):
        for candidate, item in value.items():
            if str(candidate).lower() == key.lower():
                matches.append(item)
            matches.extend(_recursive_find_key(item, key))
    elif isinstance(value, list):
        for item in value:
            matches.extend(_recursive_find_key(item, key))
    return matches


def _recursive_values(value: Any) -> list[Any]:
    matches = [value]
    if isinstance(value, dict):
        for item in value.values():
            matches.extend(_recursive_values(item))
    elif isinstance(value, list):
        for item in value:
            matches.extend(_recursive_values(item))
    return matches


def _resolve_path_token(value: Any, token: PathToken) -> list[Any]:
    kind, selector = token
    if kind == "key":
        key = str(selector)
        if isinstance(value, dict):
            return _match_dict_key(value, key)
        if isinstance(value, list):
            matches = []
            for item in value:
                if isinstance(item, dict):
                    matches.extend(_match_dict_key(item, key))
            return matches
        return []
    if kind == "index":
        if not isinstance(value, list):
            return []
        index = int(selector)
        if index < 0:
            index = len(value) + index
        return [value[index]] if 0 <= index < len(value) else []
    if kind == "wildcard":
        if isinstance(value, list):
            return list(value)
        if isinstance(value, dict):
            return list(value.values())
        return []
    if kind == "recursive_key":
        return _recursive_find_key(value, str(selector))
    if kind == "recursive_wildcard":
        return _recursive_values(value)
    return []


def resolve_field_path(payload: Any, expression: str) -> list[Any]:
    """Resolve a JSONPath-like extractor expression against a payload."""
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
    values = []
    for field_name in field_names:
        if _looks_like_path_expression(field_name):
            for value in resolve_field_path(payload, field_name):
                values.extend(flatten_strings(value))
    if not isinstance(payload, dict):
        return values

    expected = {name.lower() for name in field_names}
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
        for keyword in re.findall(r"\b[a-zA-Z_]+\b", sql.lower()):
            if keyword in SQL_KEYWORDS:
                db_operations.add(keyword)

    return ToolFacts(
        commands=commands,
        paths=paths,
        path_sensitivities=sorted(set(path_sensitivities)),
        domains=sorted(set(domains)),
        db_operations=sorted(db_operations),
    )
