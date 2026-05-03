from __future__ import annotations

import json
from pathlib import Path

from jinguzhou.adapters.mcp import build_mcp_tool_call_request
from jinguzhou.integrations.mcp import JinguzhouMCPMiddleware, ToolPolicyViolation, guard_runtime
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_file


def main() -> None:
    request = build_mcp_tool_call_request(
        "mcp.fetch.get",
        {"request": {"url": "http://169.254.169.254/latest/meta-data"}},
        call_id="demo-mcp-call",
    )
    middleware = JinguzhouMCPMiddleware(
        PolicyEngine(load_policy_file(Path("rules/tool_network_access.yaml")))
    )
    runtime = guard_runtime(lambda payload: {"ok": True, "id": payload["id"]}, middleware)

    try:
        runtime.handle(request, request_id="demo-mcp-request")
    except ToolPolicyViolation as exc:
        print(
            json.dumps(
                {
                    "action": exc.result.action,
                    "rule_id": exc.result.matched_rules[0].rule_id if exc.result.matched_rules else "",
                    "tool_name": exc.tool_call.tool_name,
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
