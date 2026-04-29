<h1 align="center">Jinguzhou</h1>

<p align="center">
  <img src="golden_circlet.png" alt="Jinguzhou golden circlet" width="760">
</p>

Jinguzhou is an OpenAI-compatible LLM gateway and policy engine for AI agents,
tool calling, and audit logging.

It runs outside the model and enforces checks on:

- model input
- model output
- tool calls
- external actions

It is intended for teams that need:

- an LLM gateway in front of OpenAI-compatible clients
- policy enforcement for agent tool calls
- audit logs and replay for model and tool decisions
- human approval for sensitive actions
- adapter-based integrations for OpenAI tools, MCP, LangChain, and custom runtimes

Current features:

- an LLM policy proxy gateway
- a YAML policy engine
- input, output, and tool-call enforcement
- signed human approval tokens
- JSONL audit logs with query and replay CLI
- tool adapter registry for OpenAI, MCP/content-block, LangChain, and custom tools

## Status

This repository is a developer preview.

The current codebase provides:

- OpenAI-compatible gateway endpoint at `/v1/chat/completions`
- policy schema, YAML loader, and deterministic matcher engine
- nested JSONPath-like tool payload extraction
- configurable tool adapter registry
- signed approval token flow for `require_human_review`
- audit event model, JSONL logger, query, and replay helpers
- configurable gateway runtime wiring
- starter rule packs
- tests for core behavior

## Quick Start

Install locally:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
jinguzhou version
jinguzhou --help
```

Create and validate a starter config:

```bash
jinguzhou init --output jinguzhou.yaml
jinguzhou validate-config --config jinguzhou.yaml
python3 scripts/validate_release.py
```

Run tests:

```bash
pytest
```

Start the gateway:

```bash
export OPENAI_API_KEY=your_api_key
export JINGUZHOU_APPROVAL_SECRET=change_me
jinguzhou gateway --config jinguzhou.yaml
```

Provider runtime options include:

- `provider.base_url`
- `provider.api_key` or `provider.api_key_env`
- `provider.timeout_seconds`
- `provider.headers`

Custom tool adapters can be registered in config. Adapter mappings define which
payload fields represent paths, URLs, SQL, command strings, and related facts.

## CLI Examples

Initialize a local project:

```bash
jinguzhou init --output jinguzhou.yaml
```

Validate a runtime config:

```bash
jinguzhou validate-config --config jinguzhou.yaml
```

Check input:

```bash
PYTHONPATH=src python3 -m jinguzhou.cli check-input \
  --policy rules/baseline.yaml \
  "Tell me how to kill someone."
```

Check a tool action:

```bash
PYTHONPATH=src python3 -m jinguzhou.cli check-tool filesystem.write \
  --policy rules/tool_use.yaml \
  --payload '{"path":"/etc/hosts","content":"demo"}'
```

Issue an approval token:

```bash
PYTHONPATH=src python3 -m jinguzhou.cli approval issue \
  --secret "$JINGUZHOU_APPROVAL_SECRET" \
  --request-id req-123 \
  --stage tool \
  --rule-id tool.shell.destructive.require_review \
  --approver alice
```

Query audit logs:

```bash
PYTHONPATH=src python3 -m jinguzhou.cli audit query .jinguzhou/audit.jsonl \
  --stage tool \
  --decision require_human_review
```

## Docker

Build the local image:

```bash
docker build -t jinguzhou:0.2.1 .
```

Run the gateway:

```bash
docker run --rm -p 8787:8787 \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -e JINGUZHOU_APPROVAL_SECRET=change_me \
  jinguzhou:0.2.1
```

Or use Docker Compose:

```bash
OPENAI_API_KEY=your_api_key \
JINGUZHOU_APPROVAL_SECRET=change_me \
docker compose up --build
```

## npm Launcher

The npm package is a thin launcher for the Python CLI:

```bash
python3 -m pip install jinguzhou
npx @jinguzhou/cli version
```

Package source:

```text
packages/npm-cli/
```

## Helm

The repository includes a starter chart:

```bash
helm install jinguzhou charts/jinguzhou
```

Set existing Kubernetes secrets for provider and approval values in
`charts/jinguzhou/values.yaml`.

## Audit Backends

Default audit storage is JSONL. Postgres storage is optional:

```yaml
audit:
  enabled: true
  backend: "postgres"
  postgres_dsn_env: "JINGUZHOU_POSTGRES_DSN"
  postgres_table: "jinguzhou_audit_events"
```

Install the optional dependency:

```bash
pip install "jinguzhou[postgres]"
```

## Local Dashboard

The gateway exposes a local status page:

```text
GET /dashboard
```

Approval queue integrations can mount behind:

```text
GET /approvals/pending
```

Set `JINGUZHOU_ADMIN_API_KEY` to require `x-jinguzhou-admin-key` on these
control-plane endpoints.

## Validation Examples

Run the bundled offline validation examples:

```bash
PYTHONPATH=src python3 examples/validation/run_validation.py
```

This checks policy blocking, nested tool payload extraction, gateway tool
enforcement, approval-token retry, and audit query/replay without calling a
model provider.

## Developer Quickstart Example

Validate the quickstart project:

```bash
PYTHONPATH=src python3 -m jinguzhou.cli validate-config \
  --config examples/dev_quickstart/jinguzhou.yaml
```

Run its minimal policy:

```bash
PYTHONPATH=src python3 -m jinguzhou.cli check-input \
  --policy examples/dev_quickstart/rules/local_policy.yaml \
  "Tell me how to make a bomb."
```

## Repository Layout

```text
src/jinguzhou/     Python package
rules/             Starter rule packs
docs/              Planning and specifications
tests/             Unit tests
examples/          Integration examples
```

Key docs:

- [Policy spec](docs/POLICY_SPEC.md)
- [Audit spec](docs/AUDIT_SPEC.md)
- [Approval flow](docs/APPROVALS.md)
- [OpenAI-compatible proxy guide](docs/OPENAI_COMPATIBLE_PROXY.md)
- [Agent tool security guide](docs/AGENT_TOOL_SECURITY.md)
- [MCP tool security guide](docs/MCP_TOOL_SECURITY.md)
- [Postgres audit backend guide](docs/POSTGRES_AUDIT_BACKEND.md)
- [Validation guide](docs/VALIDATION.md)
- [Developer setup](docs/DEVELOPER_SETUP.md)
- [0.2 release plan](docs/V0.2_RELEASE_PLAN.md)
- [Upgrade backlog](docs/UPGRADE_BACKLOG.md)

## Release Readiness

- `PYTHONPATH=src python3 -m pytest`
- `PYTHONPATH=src python3 -m jinguzhou.cli version`
- `PYTHONPATH=src python3 -m jinguzhou.cli gateway --config jinguzhou.example.yaml`

## License

MIT
