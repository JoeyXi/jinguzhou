# Approval Flow

Jinguzhou supports signed approval tokens for decisions that return
`require_human_review`.

## Flow

1. A request triggers a `require_human_review` policy decision.
2. The gateway returns a `409` response with approval context:
   - `request_id`
   - `stage`
   - `matched_rule_ids`
   - expected approval header
3. A human reviewer issues a signed approval token.
4. The client retries the same request with `x-jinguzhou-approval-token`.
5. The gateway verifies the token and continues the guarded flow.

## Configure Secret

```bash
export JINGUZHOU_APPROVAL_SECRET=change_me
```

The example runtime config reads this value through `approvals.secret_env`.

## Issue A Token

```bash
PYTHONPATH=src python3 -m jinguzhou.cli approval issue \
  --secret "$JINGUZHOU_APPROVAL_SECRET" \
  --request-id req-123 \
  --stage tool \
  --rule-id tool.shell.destructive.require_review \
  --approver alice \
  --reason "Reviewed shell command in sandbox"
```

## Retry With Token

Send the token in:

```text
x-jinguzhou-approval-token: <token>
```

## Safety Notes

- Use short TTLs for approval tokens.
- Prefer stage-specific and rule-specific approvals.
- Do not reuse approval secrets across environments.
- Treat approval tokens as sensitive credentials until they expire.
