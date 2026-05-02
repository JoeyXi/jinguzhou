# Release Notes: v0.3.0-beta

Jinguzhou 0.3.0-beta continues the Agent Ecosystem track with concrete MCP and
LangChain entry points.

## Highlights

- MCP adapter helper module for JSON-RPC `tools/call`
- LangChain-style middleware that checks policy before tool execution
- Runnable MCP tool security example
- Runnable LangChain tool policy example
- Release validation coverage for both examples

## Validation

Run:

```bash
python3 -m pytest
python3 scripts/validate_release.py
```

Expected release validation includes:

```text
v0_3_beta_examples
```
