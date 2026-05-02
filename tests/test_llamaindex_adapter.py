from pathlib import Path

from jinguzhou.adapters.llamaindex import (
    LlamaIndexToolAdapter,
    build_llamaindex_tool_call,
    normalize_llamaindex_tool_call,
)
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_file
from jinguzhou.policy.models import EvaluationContext


def test_llamaindex_adapter_normalizes_direct_tool_call() -> None:
    tool_call = normalize_llamaindex_tool_call(
        "filesystem.write",
        {"path": "/etc/hosts", "content": "demo"},
        call_id="li_1",
    )

    assert tool_call.id == "li_1"
    assert tool_call.protocol == "llamaindex"
    assert tool_call.tool_name == "filesystem.write"
    assert "path" in tool_call.extraction.path_fields


def test_llamaindex_adapter_normalizes_tool_selection_for_policy() -> None:
    adapter = LlamaIndexToolAdapter()
    payload = build_llamaindex_tool_call(
        "filesystem.write",
        {"path": "/etc/hosts", "content": "demo"},
        call_id="li_system_write",
    )

    tool_call = adapter.normalize_tool_selection(payload)
    engine = PolicyEngine(load_policy_file(Path("rules/tool_file_access.yaml")))
    result = engine.evaluate(
        EvaluationContext(
            stage="tool",
            tool_name=tool_call.tool_name,
            tool_payload=tool_call.arguments,
            tool_extraction=tool_call.extraction,
        )
    )

    assert result.action == "block"
    assert result.matched_rules[0].rule_id == "tool.file.system_write.block"


def test_llamaindex_adapter_rejects_payload_without_tool_call() -> None:
    adapter = LlamaIndexToolAdapter()

    try:
        adapter.normalize_tool_selection({"framework": "llamaindex", "tool_calls": []})
    except ValueError as exc:
        assert "does not contain" in str(exc)
    else:
        raise AssertionError("Expected invalid LlamaIndex payload to raise ValueError.")
