"""Policy file loading utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import yaml

from jinguzhou.policy.models import PolicyDocument


def load_policy_file(path: Path) -> PolicyDocument:
    """Load a policy YAML file from disk."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    document = PolicyDocument.model_validate(raw)
    if not document.sources:
        document.sources = [str(path)]
    return document


def load_policy_files(paths: Iterable[Path]) -> PolicyDocument:
    """Load and merge multiple policy files into one combined document."""
    resolved_paths = list(paths)
    if not resolved_paths:
        raise ValueError("At least one policy file is required.")

    documents = [load_policy_file(path) for path in resolved_paths]
    merged_rules = []
    seen_rule_ids = {}
    descriptions = []

    for document in documents:
        if document.description:
            descriptions.append(document.description)
        for rule in document.rules:
            existing_source = seen_rule_ids.get(rule.id)
            if existing_source:
                raise ValueError(
                    f"Duplicate rule id '{rule.id}' found in '{existing_source}' and "
                    f"'{document.sources[0]}'."
                )
            seen_rule_ids[rule.id] = document.sources[0]
            merged_rules.append(rule)

    names = [document.name for document in documents]
    return PolicyDocument(
        version=max(document.version for document in documents),
        name="+".join(names),
        description="\n".join(descriptions),
        sources=[source for document in documents for source in document.sources],
        rules=merged_rules,
    )
