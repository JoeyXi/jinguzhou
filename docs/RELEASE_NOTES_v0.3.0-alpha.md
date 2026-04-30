# Release Notes: v0.3.0-alpha

Jinguzhou 0.3.0-alpha starts the Agent Ecosystem track.

## Highlights

- Agent adapter foundation under `jinguzhou.adapters`
- Normalized tool-call handling for framework payloads
- MCP JSON-RPC `tools/call` extraction
- LlamaIndex-style top-level tool-call extraction
- OpenAI Agents-style `function_call` extraction
- Expanded JSONPath-like extractor support
- File, network, and database policy packs

## Policy Packs

- `rules/tool_file_access.yaml`
- `rules/tool_network_access.yaml`
- `rules/tool_database_access.yaml`

## Validation

Run:

```bash
python3 -m pytest
python3 scripts/validate_release.py
```

Expected release validation includes:

```text
v0_3_policy_packs
```
