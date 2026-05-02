# MCP Tool Security Example

This example shows how to normalize an MCP `tools/call` request and evaluate it
with the Jinguzhou network policy pack before a tool runtime executes it.

Run from the repository root:

```bash
PYTHONPATH=src python3 examples/mcp-tool-security/demo.py
```

Expected output:

```json
{"action": "block", "rule_id": "tool.network.metadata_endpoint.block", "tool_name": "network.request"}
```
