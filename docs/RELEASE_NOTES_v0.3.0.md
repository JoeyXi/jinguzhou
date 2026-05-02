# Release Notes: v0.3.0

Jinguzhou 0.3.0 completes the Agent Ecosystem release.

## Highlights

- Adapter helpers for MCP, LlamaIndex, and OpenAI Agents
- LangChain-style pre-execution tool middleware
- JSONPath-like extractor support for nested agent tool payloads
- File, network, and database policy packs
- Runnable examples for MCP, LangChain, LlamaIndex, and OpenAI Agents
- Release validation across all v0.3 examples

## Validation

Run:

```bash
python3 -m pytest
python3 scripts/validate_release.py
```

Expected release validation includes:

```text
v0_3_final_examples
```
