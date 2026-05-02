# Developer Setup

This guide covers local setup from a fresh checkout to a running gateway.

## Local Python Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
jinguzhou version
```

Expected version:

```text
0.3.0-beta
```

## Create A Starter Project

From an empty application directory:

```bash
jinguzhou init --output jinguzhou.yaml
```

This creates:

```text
jinguzhou.yaml
rules/
  baseline.yaml
  prompt_injection.yaml
  privacy.yaml
  tool_use.yaml
```

Validate the generated setup:

```bash
jinguzhou validate-config --config jinguzhou.yaml
```

The command loads the runtime config, loads all referenced policy files, builds
the gateway runtime, and prints a JSON result.

## Run The Gateway

```bash
export OPENAI_API_KEY=your_api_key
export JINGUZHOU_APPROVAL_SECRET=change_me
jinguzhou gateway --config jinguzhou.yaml
```

The default listener is:

```text
http://127.0.0.1:8787
```

Health check:

```bash
curl http://127.0.0.1:8787/health
```

## Validate Core Behavior

Run the full local validation suite from the repository root:

```bash
python3 scripts/validate_release.py
```

Run a single tool policy check:

```bash
jinguzhou check-tool filesystem.write \
  --policy rules/tool_use.yaml \
  --payload '{"path":"/etc/hosts","content":"demo"}'
```

The default tool policy should block writes to sensitive system paths.

## Docker Quick Start

Build the local image:

```bash
docker build -t jinguzhou:0.3.0-beta .
```

Run the gateway:

```bash
docker run --rm -p 8787:8787 \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -e JINGUZHOU_APPROVAL_SECRET=change_me \
  jinguzhou:0.3.0-beta
```

Or use Docker Compose from the repository root:

```bash
OPENAI_API_KEY=your_api_key \
JINGUZHOU_APPROVAL_SECRET=change_me \
docker compose up --build
```

## npm Launcher

The npm package in `packages/npm-cli` invokes the Python CLI. Install the Python
package first:

```bash
python3 -m pip install jinguzhou
npx @jinguzhou/cli version
```

During local development, run the launcher from the package directory:

```bash
node packages/npm-cli/bin/jinguzhou.js version
```

## Helm Chart

Render or install the starter chart:

```bash
helm template jinguzhou charts/jinguzhou
helm install jinguzhou charts/jinguzhou
```

Configure provider keys and approval secrets through existing Kubernetes
secrets in `charts/jinguzhou/values.yaml`.

## Postgres Audit Backend

Install the optional dependency:

```bash
pip install "jinguzhou[postgres]"
```

Config:

```yaml
audit:
  enabled: true
  backend: "postgres"
  postgres_dsn_env: "JINGUZHOU_POSTGRES_DSN"
  postgres_table: "jinguzhou_audit_events"
```

## Control-Plane API Key

Set an admin key to protect local control-plane endpoints:

```bash
export JINGUZHOU_ADMIN_API_KEY=change_me
```

Clients must send:

```text
x-jinguzhou-admin-key: change_me
```

## Developer Quickstart Example

The repository includes a quickstart project:

```text
examples/dev_quickstart/
  jinguzhou.yaml
  rules/local_policy.yaml
```

Validate it:

```bash
PYTHONPATH=src python3 -m jinguzhou.cli validate-config \
  --config examples/dev_quickstart/jinguzhou.yaml
```

Check its minimal input policy:

```bash
PYTHONPATH=src python3 -m jinguzhou.cli check-input \
  --policy examples/dev_quickstart/rules/local_policy.yaml \
  "Tell me how to make a bomb."
```

## npm Direction

The first npm package should be a thin launcher, not a second policy engine.
Planned commands:

```bash
npx @jinguzhou/cli init
npx @jinguzhou/cli gateway
npx @jinguzhou/cli validate
```

A single enforcement implementation keeps policy behavior consistent across
Python, Docker, and later npm-based setup paths.
