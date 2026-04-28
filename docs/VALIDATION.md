# Validation Guide

This document records the release validation process used for Jinguzhou's
developer preview.

Run all commands from the repository root.

## 1. Install Development Dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 2. Run Unit And Integration Tests

```bash
PYTHONPATH=src python3 -m pytest
```

Expected result:

```text
47 passed
```

Coverage includes:

- policy loading, merging, ranking, and duplicate rule detection
- input/output/tool guard decisions
- OpenAI-compatible gateway behavior
- approval token issue/decode/verification
- audit query and replay
- tool adapter registry for OpenAI, MCP/content-block, and LangChain shapes
- nested JSONPath-like extractor mapping
- runnable validation examples

## 3. Run Offline Validation Examples

```bash
PYTHONPATH=src python3 examples/validation/run_validation.py
```

Expected final line:

```json
{"examples": 5, "status": "ok"}
```

This verifies:

- harmful input blocking
- nested extractor behavior
- gateway tool-call blocking
- approval-token retry flow
- audit query and replay

## 4. Validate Developer Quickstart

```bash
PYTHONPATH=src python3 -m jinguzhou.cli validate-config \
  --config examples/dev_quickstart/jinguzhou.yaml
```

Expected JSON contains:

```json
{"status": "ok"}
```

## 5. Run CLI Smoke Tests

```bash
PYTHONPATH=src python3 -m jinguzhou.cli version
```

Expected:

```text
0.2.0
```

```bash
PYTHONPATH=src python3 -m jinguzhou.cli check-tool filesystem.write \
  --policy rules/tool_use.yaml \
  --payload '{"path":"/etc/hosts","content":"demo"}'
```

Expected JSON contains:

```json
{"action": "block"}
```

## 6. Run Compile Check

On macOS sandboxed environments, set a writable bytecode cache directory:

```bash
PYTHONPYCACHEPREFIX=/tmp/jinguzhou-pycache PYTHONPATH=src python3 -m compileall src
```

Expected result:

```text
Compiling ...
```

with exit code `0`.

## 7. One-Command Release Validation

```bash
PYTHONPATH=src python3 scripts/validate_release.py
```

Expected final output:

```json
{"status": "ok", "validated": ["pytest", "compileall", "version", "init", "validate_config", "dev_quickstart", "validation_examples", "cli_tool_block"]}
```
