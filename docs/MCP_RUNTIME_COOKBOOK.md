# MCP Runtime Cookbook

This page shows the intended runtime-level integration shape for MCP.

## Goal

Check an MCP JSON-RPC `tools/call` request before the request reaches the real
tool executor.

## Minimal Pattern

```python
from jinguzhou.adapters.mcp import build_mcp_tool_call_request
from jinguzhou.integrations.mcp import JinguzhouMCPMiddleware, guard_runtime
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_file


def execute_request(payload: dict) -> dict:
    return {"ok": True, "id": payload["id"]}


middleware = JinguzhouMCPMiddleware(
    PolicyEngine(load_policy_file("rules/tool_network_access.yaml"))
)
runtime = guard_runtime(execute_request, middleware)

request = build_mcp_tool_call_request(
    "mcp.fetch.get",
    {"request": {"url": "https://demo.ngrok.io/api"}},
)

result = runtime.handle(
    request,
    request_id="req-123",
    approval_token="signed-token-if-required",
)
```

## What The Middleware Does

- normalizes the MCP request through the shared adapter registry
- evaluates the normalized tool call against tool-stage policy rules
- blocks execution on `block`
- requires a valid approval token on `require_human_review`
- writes audit events when audit logging is configured

## Runnable Example

```bash
PYTHONPATH=src python3 examples/mcp-tool-security/demo.py
```
