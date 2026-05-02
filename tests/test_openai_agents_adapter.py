from pathlib import Path

from jinguzhou.adapters.openai_agents import (
    OpenAIAgentsToolAdapter,
    build_openai_agents_function_call,
    normalize_openai_agents_function_call,
)
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_file
from jinguzhou.policy.models import EvaluationContext


def test_openai_agents_adapter_normalizes_direct_function_call() -> None:
    tool_call = normalize_openai_agents_function_call(
        "db.run_sql",
        {"sql": "DROP TABLE users"},
        call_id="agent_1",
    )

    assert tool_call.id == "agent_1"
    assert tool_call.protocol == "openai_agents"
    assert tool_call.tool_name == "database.query"
    assert "sql" in tool_call.extraction.sql_fields


def test_openai_agents_adapter_normalizes_response_item_for_policy() -> None:
    adapter = OpenAIAgentsToolAdapter()
    item = build_openai_agents_function_call(
        "db.run_sql",
        {"sql": "DROP TABLE users"},
        call_id="agent_drop",
    )

    tool_call = adapter.normalize_response_item(item)
    engine = PolicyEngine(load_policy_file(Path("rules/tool_database_access.yaml")))
    result = engine.evaluate(
        EvaluationContext(
            stage="tool",
            tool_name=tool_call.tool_name,
            tool_payload=tool_call.arguments,
            tool_extraction=tool_call.extraction,
        )
    )

    assert result.action == "block"
    assert result.matched_rules[0].rule_id == "tool.database.destructive_operation.block"


def test_openai_agents_adapter_rejects_non_function_call_item() -> None:
    adapter = OpenAIAgentsToolAdapter()

    try:
        adapter.normalize_response_item({"type": "message", "content": "hello"})
    except ValueError as exc:
        assert "does not contain" in str(exc)
    else:
        raise AssertionError("Expected invalid OpenAI Agents item to raise ValueError.")
