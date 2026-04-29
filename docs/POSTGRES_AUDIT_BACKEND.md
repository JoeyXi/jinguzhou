# Postgres Audit Backend

Jinguzhou writes audit records to JSONL by default. A Postgres backend is
available when local files are not enough.

## Install

```bash
pip install "jinguzhou[postgres]"
```

## Config

```yaml
audit:
  enabled: true
  backend: "postgres"
  postgres_dsn_env: "JINGUZHOU_POSTGRES_DSN"
  postgres_table: "jinguzhou_audit_events"
```

## Stored Fields

The Postgres backend stores:

- `event_id`
- `timestamp`
- `request_id`
- `stage`
- `decision`
- `payload`

The `payload` column contains the full JSON event record.

## Common Uses

- central audit storage across multiple gateway instances
- SQL queries for review workflows
- downstream export into analytics or compliance systems

## Related Docs

- [Audit spec](AUDIT_SPEC.md)
- [Developer setup](DEVELOPER_SETUP.md)
