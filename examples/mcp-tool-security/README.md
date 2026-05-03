# MCP Tool Security Example

This example shows how to guard an MCP `tools/call` request with the Jinguzhou
runtime middleware before a tool executor runs it.

Run from the repository root:

```bash
PYTHONPATH=src python3 examples/mcp-tool-security/demo.py
```

Expected output:

```json
{"action": "block", "rule_id": "tool.network.metadata_endpoint.block", "tool_name": "network.request"}
```
