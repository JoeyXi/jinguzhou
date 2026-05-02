from pathlib import Path

from jinguzhou.adapters.mcp import (
    MCPToolAdapter,
    build_mcp_tool_call_request,
    normalize_mcp_tool_call,
)
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_file
from jinguzhou.policy.models import EvaluationContext


def test_mcp_adapter_normalizes_direct_tool_call() -> None:
    tool_call = normalize_mcp_tool_call(
        "mcp.fetch.get",
        {"request": {"url": "https://demo.ngrok.io/collect"}},
        call_id="mcp_1",
    )

    assert tool_call.id == "mcp_1"
    assert tool_call.protocol == "mcp"
    assert tool_call.tool_name == "network.request"
    assert "$.request.url" in tool_call.extraction.url_fields


def test_mcp_adapter_normalizes_jsonrpc_tools_call_for_policy() -> None:
    adapter = MCPToolAdapter()
    request = build_mcp_tool_call_request(
        "mcp.fetch.get",
        {"request": {"url": "http://169.254.169.254/latest/meta-data"}},
        call_id="mcp_metadata",
    )

    tool_call = adapter.normalize_jsonrpc_request(request)
    engine = PolicyEngine(load_policy_file(Path("rules/tool_network_access.yaml")))
    result = engine.evaluate(
        EvaluationContext(
            stage="tool",
            tool_name=tool_call.tool_name,
            tool_payload=tool_call.arguments,
            tool_extraction=tool_call.extraction,
        )
    )

    assert result.action == "block"
    assert result.matched_rules[0].rule_id == "tool.network.metadata_endpoint.block"


def test_mcp_adapter_rejects_payload_without_tool_call() -> None:
    adapter = MCPToolAdapter()

    try:
        adapter.normalize_jsonrpc_request({"jsonrpc": "2.0", "method": "ping"})
    except ValueError as exc:
        assert "does not contain" in str(exc)
    else:
        raise AssertionError("Expected invalid MCP payload to raise ValueError.")
