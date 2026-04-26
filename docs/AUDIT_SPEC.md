# Audit Specification

Jinguzhou audit records should make safety decisions explainable and reviewable.

## MVP Storage

- JSONL file

## Event Fields

- `event_id`
- `timestamp`
- `request_id`
- `stage`
- `decision`
- `policy_name`
- `matched_rule_ids`
- `category`
- `severity`
- `provider`
- `model`
- `message`
- `metadata`

## Privacy Defaults

- Do not log secrets
- Redact common credential patterns by default
- Full prompt logging should remain opt-in

## Event Types

- `policy_decision`
- `gateway_error`
- `approval`
- `system_event`

## Query CLI

Audit logs can be queried directly:

```bash
PYTHONPATH=src python3 -m jinguzhou.cli audit query .jinguzhou/audit.jsonl \
  --request-id req-123 \
  --stage tool \
  --decision require_human_review
```

Supported filters:

- `request_id`
- `stage`
- `decision`
- `rule_id`
- `limit`

## Replay CLI

Replay renders a compact timeline for a request:

```bash
PYTHONPATH=src python3 -m jinguzhou.cli audit replay .jinguzhou/audit.jsonl \
  --request-id req-123
```

This is intended for first-pass incident review and policy debugging.
