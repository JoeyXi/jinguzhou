# MCP Tool Security

Jinguzhou can evaluate tool calls carried through MCP-style content blocks or
MCP JSON-RPC `tools/call` requests after they are normalized by the adapter
registry.

## What Matters For MCP

- the raw tool payload may not use the same field names as OpenAI tool calls
- extractor mappings define which fields represent commands, paths, URLs, SQL,
  and related facts
- policy rules run against the normalized tool facts rather than the original
  payload shape

## Why The Extractor Layer Exists

Different agent runtimes describe the same action in different ways. The
extractor layer keeps those differences in adapter config instead of matcher
logic.

## Example

An MCP tool payload might expose a target file under `target_path` instead of
`path`. The adapter can map that field into the normalized path list, and the
policy rule stays unchanged.

Python helper:

```python
from jinguzhou.adapters.mcp import MCPToolAdapter, build_mcp_tool_call_request

adapter = MCPToolAdapter()
request = build_mcp_tool_call_request(
    "mcp.fetch.get",
    {"request": {"url": "http://169.254.169.254/latest/meta-data"}},
)
tool_call = adapter.normalize_jsonrpc_request(request)
```

Runnable example:

```bash
PYTHONPATH=src python3 examples/mcp-tool-security/demo.py
```

## Typical Policy Checks

- block writes to system paths
- require review for requests to paste or tunnel domains
- block destructive database operations

## Related Docs

- [Policy spec](POLICY_SPEC.md)
- [Agent tool security guide](AGENT_TOOL_SECURITY.md)
