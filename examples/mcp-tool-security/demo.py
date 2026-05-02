from __future__ import annotations

import json
from pathlib import Path

from jinguzhou.adapters.mcp import MCPToolAdapter, build_mcp_tool_call_request
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_file
from jinguzhou.policy.models import EvaluationContext


def main() -> None:
    adapter = MCPToolAdapter()
    request = build_mcp_tool_call_request(
        "mcp.fetch.get",
        {"request": {"url": "http://169.254.169.254/latest/meta-data"}},
        call_id="demo-mcp-call",
    )
    tool_call = adapter.normalize_jsonrpc_request(request)

    engine = PolicyEngine(load_policy_file(Path("rules/tool_network_access.yaml")))
    result = engine.evaluate(
        EvaluationContext(
            stage="tool",
            tool_name=tool_call.tool_name,
            tool_payload=tool_call.arguments,
            provider="mcp",
            tool_extraction=tool_call.extraction,
        )
    )

    print(
        json.dumps(
            {
                "action": result.action,
                "rule_id": result.matched_rules[0].rule_id if result.matched_rules else "",
                "tool_name": tool_call.tool_name,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
