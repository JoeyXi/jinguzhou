# Audit Specification

Jinguzhou audit records capture policy decisions for review and debugging.

## MVP Storage

- JSONL file
- Optional Postgres table

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

## Postgres Backend

Config:

```yaml
audit:
  enabled: true
  backend: "postgres"
  postgres_dsn_env: "JINGUZHOU_POSTGRES_DSN"
  postgres_table: "jinguzhou_audit_events"
```

Install:

```bash
pip install "jinguzhou[postgres]"
```

The backend creates the target table if it does not exist. The table stores the
stable event fields used for filtering plus the full JSON payload.

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

Use replay for initial incident review and policy debugging.
