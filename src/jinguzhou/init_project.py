"""Project initialization helpers for Jinguzhou."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


STARTER_CONFIG = """gateway:
  host: "127.0.0.1"
  port: 8787

policy:
  files:
    - "rules/baseline.yaml"
    - "rules/prompt_injection.yaml"
    - "rules/privacy.yaml"
    - "rules/tool_use.yaml"

provider:
  type: "openai-compatible"
  base_url: "https://api.openai.com"
  api_key_env: "OPENAI_API_KEY"
  timeout_seconds: 60
  headers: {}

audit:
  enabled: true
  path: ".jinguzhou/audit.jsonl"
  redact: true

approvals:
  enabled: true
  secret_env: "JINGUZHOU_APPROVAL_SECRET"
  ttl_seconds: 900

tool_adapters: []
"""


STARTER_RULES = {
    "baseline.yaml": """version: 1
name: baseline-human-safety
description: Core protections for harmful human-directed requests.
rules:
  - id: human_harm.instructions.block
    stage: input
    category: human_harm
    severity: critical
    action: block
    reason: Request appears to ask for instructions that could directly harm people.
    match:
      any_keywords:
        - "how to kill"
        - "make a bomb"
        - "poison someone"

  - id: output.harmful_instructions.block
    stage: output
    category: human_harm
    severity: critical
    action: block
    reason: Output appears to contain dangerous instructions that could harm people.
    match:
      any_keywords:
        - "steps to make a bomb"
        - "best poison dosage"
""",
    "prompt_injection.yaml": """version: 1
name: prompt-injection
description: Detect attempts to override system rules or exfiltrate hidden context.
rules:
  - id: prompt_injection.override.warn
    stage: input
    category: prompt_injection
    severity: high
    action: warn
    reason: Request appears to try to override hidden instructions or safety rules.
    match:
      any_keywords:
        - "ignore previous instructions"
        - "reveal the system prompt"
        - "disregard safety policy"
""",
    "privacy.yaml": """version: 1
name: privacy
description: Protect secrets and personal data in output.
rules:
  - id: output.secret_leak.redact
    stage: output
    category: privacy
    severity: high
    action: redact
    reason: Output appears to contain secret material or credential-like data.
    match:
      regex:
        - "sk-[A-Za-z0-9]{16,}"
        - "AKIA[0-9A-Z]{16}"
""",
    "tool_use.yaml": """version: 1
name: tool-use
description: Default policy for tool and action safety.
rules:
  - id: tool.shell.destructive.require_review
    stage: tool
    category: tool_use
    severity: high
    action: require_human_review
    reason: Shell command appears capable of destructive system modification.
    match:
      tool_name: shell
      command_contains:
        - "rm "
        - "chmod "
        - "curl "

  - id: tool.filesystem.system_write.block
    stage: tool
    category: filesystem
    severity: critical
    action: block
    reason: Writes to system paths are blocked by default.
    match:
      tool_name: filesystem.write
      path_sensitivity_in:
        - system

  - id: tool.filesystem.secrets.review
    stage: tool
    category: filesystem
    severity: high
    action: require_human_review
    reason: Access to likely secret-bearing paths requires review.
    match:
      tool_name: filesystem.read
      path_sensitivity_in:
        - secrets

  - id: tool.network.public_tunnel.review
    stage: tool
    category: network
    severity: high
    action: require_human_review
    reason: Requests to public tunnel or paste domains require review.
    match:
      tool_name: network.request
      domain_suffix_in:
        - ngrok.io
        - pastebin.com

  - id: tool.database.destructive.block
    stage: tool
    category: database
    severity: critical
    action: block
    reason: Destructive database operations are blocked by default.
    match:
      tool_name: database.query
      db_operation_in:
        - drop
        - truncate
        - alter

  - id: tool.payment.block
    stage: tool
    category: finance
    severity: critical
    action: block
    reason: Payments should be blocked by default in the baseline policy.
    match:
      tool_name: payment.execute
""",
}


@dataclass(frozen=True)
class InitResult:
    """Files created by the project initializer."""

    config_path: Path
    rule_paths: list[Path]


def write_starter_project(
    output: Path,
    *,
    include_rules: bool = True,
    force: bool = False,
) -> InitResult:
    """Write a starter Jinguzhou config and optional rule pack files."""
    config_path = output
    target_dir = config_path.parent
    target_dir.mkdir(parents=True, exist_ok=True)

    if config_path.exists() and not force:
        raise FileExistsError(f"Config already exists: {config_path}")

    if include_rules and not force:
        rules_dir = target_dir / "rules"
        for filename in STARTER_RULES:
            rule_path = rules_dir / filename
            if rule_path.exists():
                raise FileExistsError(f"Rule file already exists: {rule_path}")

    config_path.write_text(STARTER_CONFIG, encoding="utf-8")

    created_rules: list[Path] = []
    if include_rules:
        rules_dir = target_dir / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in STARTER_RULES.items():
            rule_path = rules_dir / filename
            if rule_path.exists() and not force:
                raise FileExistsError(f"Rule file already exists: {rule_path}")
            rule_path.write_text(content, encoding="utf-8")
            created_rules.append(rule_path)

    return InitResult(config_path=config_path, rule_paths=created_rules)
