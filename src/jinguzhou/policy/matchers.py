"""Deterministic matchers for policy evaluation."""

from __future__ import annotations

import re
from typing import Any

from jinguzhou.policy.extractors import extract_tool_facts, normalize_path
from jinguzhou.policy.models import EvaluationContext, MatchConfig


def _normalize_text(context: EvaluationContext) -> str:
    payload = context.tool_payload
    if isinstance(payload, dict):
        payload_text = " ".join(f"{key}={value}" for key, value in payload.items())
    else:
        payload_text = str(payload)
    return " ".join(
        part for part in [context.text, context.tool_name, payload_text] if part
    ).lower()


def matches(context: EvaluationContext, match: MatchConfig) -> bool:
    """Return True when the context satisfies the matcher config."""
    text = _normalize_text(context)
    tool_facts = extract_tool_facts(context) if context.stage == "tool" else None

    if match.any_keywords and not any(term.lower() in text for term in match.any_keywords):
        return False

    if match.all_keywords and not all(term.lower() in text for term in match.all_keywords):
        return False

    if match.regex and not any(re.search(pattern, text, re.IGNORECASE) for pattern in match.regex):
        return False

    if match.tool_name and context.tool_name != match.tool_name:
        return False

    if match.command_contains:
        command_lower = " ".join(tool_facts.commands if tool_facts is not None else []).lower()
        if not any(token.lower() in command_lower for token in match.command_contains):
            return False

    if match.path_starts_with or match.path_regex or match.path_sensitivity_in:
        paths = tool_facts.paths if tool_facts is not None else []

        if match.path_starts_with:
            normalized_paths = [normalize_path(path) for path in paths]
            prefixes = [normalize_path(prefix) for prefix in match.path_starts_with]
            if not any(
                path.startswith(prefix)
                for path in normalized_paths
                for prefix in prefixes
            ):
                return False

        if match.path_regex:
            if not any(
                re.search(pattern, path, re.IGNORECASE)
                for pattern in match.path_regex
                for path in paths
            ):
                return False

        if match.path_sensitivity_in:
            sensitivities = tool_facts.path_sensitivities if tool_facts is not None else []
            expected = {value.lower() for value in match.path_sensitivity_in}
            if not any(sensitivity in expected for sensitivity in sensitivities):
                return False

    if match.domain_in or match.domain_suffix_in or match.domain_regex:
        domains = tool_facts.domains if tool_facts is not None else []
        if match.domain_in:
            allowed = {value.lower() for value in match.domain_in}
            if not any(domain in allowed for domain in domains):
                return False
        if match.domain_suffix_in:
            suffixes = tuple(value.lower() for value in match.domain_suffix_in)
            if not any(domain.endswith(suffixes) for domain in domains):
                return False
        if match.domain_regex:
            if not any(
                re.search(pattern, domain, re.IGNORECASE)
                for pattern in match.domain_regex
                for domain in domains
            ):
                return False

    if match.db_operation_in:
        operations = tool_facts.db_operations if tool_facts is not None else []
        expected = {value.lower() for value in match.db_operation_in}
        if not any(operation in expected for operation in operations):
            return False

    if match.metadata_equals:
        for key, expected in match.metadata_equals.items():
            if context.metadata.get(key) != expected:
                return False

    if match.model_in and context.model not in match.model_in:
        return False

    if match.provider_in and context.provider not in match.provider_in:
        return False

    return True
