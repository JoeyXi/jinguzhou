from pathlib import Path

from jinguzhou.guards.tool_guard import ToolGuard
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_file


def test_tool_guard_blocks_payment_by_default() -> None:
    policy = load_policy_file(Path("rules/tool_use.yaml"))
    guard = ToolGuard(PolicyEngine(policy))

    result = guard.evaluate("payment.execute", {"amount": 100})

    assert result.action == "block"


def test_tool_guard_reviews_public_tunnel_network_request() -> None:
    policy = load_policy_file(Path("rules/tool_use.yaml"))
    guard = ToolGuard(PolicyEngine(policy))

    result = guard.evaluate("network.request", {"url": "https://pastebin.com/raw/demo"})

    assert result.action == "require_human_review"
