# AGENTS.md

## Cursor Cloud specific instructions

Jinguzhou is a single Python service: an OpenAI-compatible LLM gateway + policy
engine (FastAPI/uvicorn) plus a `jinguzhou` Typer CLI. Python 3.12 is used here
(project supports >=3.9). There is no separate frontend/backend split and no
database is required for default runs (audit uses JSONL; Postgres is optional).

### Environment / dependencies

- Dependencies install into a virtualenv at `.venv/` (gitignored). The startup
  update script creates it and runs `pip install -e ".[dev]"`. Activate it with
  `source .venv/bin/activate` before running any command below.
- The system package `python3.12-venv` is required to create the venv; it is
  already provisioned in this environment.

### Run / test / build (standard commands, see README.md + CONTRIBUTING.md)

- Tests: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest` (CI sets this env
  var; pytest is configured via `[tool.pytest.ini_options]` in `pyproject.toml`
  with `pythonpath = ["src"]`, so no manual `PYTHONPATH` is needed for pytest).
- Full release/validation suite (compileall "lint" + CLI + all examples):
  `PYTHONPATH=src python3 scripts/validate_release.py`. There is no dedicated
  linter (ruff/flake8/black are not configured despite `.ruff_cache` in
  `.gitignore`); `compileall` is the closest lint-style check and is included in
  the validation script.
- Run the gateway (dev): `jinguzhou gateway --config <config>` listens on
  `http://127.0.0.1:8787` by default. Health check: `GET /health`.

### Non-obvious gotchas

- Do NOT run the gateway with `jinguzhou.example.yaml`. That example config loads
  both `rules/tool_use.yaml` and `rules/tool_network_access.yaml`, which share a
  duplicate rule id (`tool.network.public_tunnel.review`), so the loader raises a
  `ValueError` on startup. For a runnable gateway, generate a clean starter
  config in a scratch dir instead: `jinguzhou init --output jinguzhou.yaml`
  (creates `jinguzhou.yaml` + a `rules/` dir), then
  `jinguzhou gateway --config jinguzhou.yaml`. Note `init` writes a `rules/`
  folder in the current working directory, so run it from a scratch dir (not the
  repo root, which already has `rules/`).
- `/dashboard` and `/approvals/pending` require the `x-jinguzhou-admin-key`
  header only when `JINGUZHOU_ADMIN_API_KEY` is set (via
  `security.admin_api_key_env`); otherwise they are open.
- The gateway needs `OPENAI_API_KEY` set to start (any placeholder works for
  policy-only testing) and `JINGUZHOU_APPROVAL_SECRET` when approvals are
  enabled. A real key is only needed for requests that actually reach the
  upstream provider; policy-blocked requests never call the provider.
