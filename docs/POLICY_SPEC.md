# Policy Specification

This document defines the first public shape of Jinguzhou policy files.

## Goals

- Human-readable
- Easy to diff in Git
- Easy to validate in code
- Safe to extend later

## File Structure

```yaml
version: 1
name: baseline-human-safety
description: Core protections for harmful requests and unsafe tool use.
rules:
  - id: human_harm.instructions.block
    stage: input
    category: human_harm
    severity: critical
    action: block
    reason: Request appears to ask for instructions that can harm people.
    match:
      any_keywords:
        - "make a bomb"
        - "poison someone"
```

## Supported Fields

Top-level fields:

- `version`: integer
- `name`: string
- `description`: optional string
- `rules`: list of rule objects

Rule fields:

- `id`: unique rule identifier
- `stage`: `input`, `output`, or `tool`
- `category`: logical risk group
- `severity`: `low`, `medium`, `high`, or `critical`
- `action`: `allow`, `warn`, `block`, `redact`, or `require_human_review`
- `reason`: human-readable explanation
- `priority`: optional integer
- `match`: matcher object

MVP matcher keys:

- `any_keywords`
- `all_keywords`
- `regex`
- `tool_name`
- `command_contains`
- `path_starts_with`
- `path_regex`
- `path_sensitivity_in`
- `domain_in`
- `domain_suffix_in`
- `db_operation_in`
- `metadata_equals`
- `model_in`
- `provider_in`

## Richer Tool Matching

Tool-stage rules can now reason about several kinds of structured intent:

- file paths and path prefixes
- inferred path sensitivity classes
- network target domains
- database operation types

Those facts are now produced by a dedicated extractor layer. Matchers consume
normalized tool facts; they no longer depend on hard-coded payload field names
inside matcher logic.

## Extractor Layer

Each tool evaluation context may carry a `tool_extraction` config that tells the
extractor which payload fields correspond to:

- commands
- paths
- path sensitivity labels
- URLs/domains
- database operation names
- SQL strings

This makes adapter-specific payload mapping configurable without changing the
matcher core.

In the gateway, those mappings can be supplied automatically by a tool adapter
registry instead of being passed manually at every evaluation site.

Example adapter-side mapping:

```python
from jinguzhou.policy.models import EvaluationContext, ToolExtractionConfig

context = EvaluationContext(
    stage="tool",
    tool_name="custom.fs.write",
    tool_payload={"target": "/etc/hosts", "body": "demo"},
    tool_extraction=ToolExtractionConfig(
        path_fields=["target"],
    ),
)
```

The same rule can then match `path_starts_with` or `path_sensitivity_in`
without caring that this tool uses `target` instead of `path`.

### Path Matching

Use `path_starts_with` or `path_regex` when a tool payload carries fields like
`path`, `file_path`, `target_path`, `directory`, or any adapter-configured
equivalent field.

Example:

```yaml
- id: filesystem.system.block
  stage: tool
  category: filesystem
  severity: critical
  action: block
  reason: Writes to system paths are blocked.
  match:
    tool_name: filesystem.write
    path_starts_with:
      - /etc
      - /usr
```

### Path Sensitivity

Use `path_sensitivity_in` when you want policy to match semantic classes instead
of exact prefixes. Current inferred labels are:

- `system`
- `secrets`
- `user_data`
- `workspace`
- `unknown`

Example:

```yaml
- id: filesystem.secrets.review
  stage: tool
  category: filesystem
  severity: high
  action: require_human_review
  reason: Secret-bearing paths require review.
  match:
    tool_name: filesystem.read
    path_sensitivity_in:
      - secrets
```

### Domain Matching

Use `domain_in` or `domain_suffix_in` for payloads that carry `url`, `endpoint`,
`base_url`, `domain`, `host`, or any adapter-configured equivalent field.

Example:

```yaml
- id: network.exfiltration.review
  stage: tool
  category: network
  severity: high
  action: require_human_review
  reason: Requests to public paste services require review.
  match:
    tool_name: network.request
    domain_suffix_in:
      - pastebin.com
      - ngrok.io
```

### Database Operation Matching

Use `db_operation_in` for payloads with `operation`, `op`, `query_type`, or SQL
strings carried in `sql`, `query`, `statement`, or adapter-configured
equivalent fields.

Example:

```yaml
- id: database.destructive.block
  stage: tool
  category: database
  severity: critical
  action: block
  reason: Destructive database operations are blocked.
  match:
    tool_name: database.query
    db_operation_in:
      - drop
      - truncate
      - alter
```

## Evaluation Model

Policies are evaluated against a normalized context object.

The strictest matched action wins by default:

1. `block`
2. `require_human_review`
3. `redact`
4. `warn`
5. `allow`

If `priority` is present, higher values sort ahead within the same action level.
