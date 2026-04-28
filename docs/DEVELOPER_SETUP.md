# Developer Setup

This guide covers the fastest local path from a fresh checkout to a working
Jinguzhou developer gateway.

## Local Python Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
jinguzhou version
```

Expected version:

```text
0.2.0
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
docker build -t jinguzhou:0.2.0 .
```

Run the gateway:

```bash
docker run --rm -p 8787:8787 \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -e JINGUZHOU_APPROVAL_SECRET=change_me \
  jinguzhou:0.2.0
```

Or use Docker Compose from the repository root:

```bash
OPENAI_API_KEY=your_api_key \
JINGUZHOU_APPROVAL_SECRET=change_me \
docker compose up --build
```

## Developer Quickstart Example

The repository includes a self-contained quickstart project:

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

The first npm package should be a thin launcher for developers, not a duplicate
policy engine. The intended future commands are:

```bash
npx @jinguzhou/cli init
npx @jinguzhou/cli gateway
npx @jinguzhou/cli validate
```

Keeping the enforcement core in one implementation makes policy behavior easier
to audit and test across Python, Docker, and future npm-based onboarding.
