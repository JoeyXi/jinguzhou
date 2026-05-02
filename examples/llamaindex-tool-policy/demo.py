from __future__ import annotations

import json
from pathlib import Path

from jinguzhou.adapters.llamaindex import (
    LlamaIndexToolAdapter,
    build_llamaindex_tool_call,
)
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_file
from jinguzhou.policy.models import EvaluationContext


def main() -> None:
    adapter = LlamaIndexToolAdapter()
    payload = build_llamaindex_tool_call(
        "filesystem.write",
        {"path": "/etc/hosts", "content": "demo"},
        call_id="demo-llamaindex-call",
    )
    tool_call = adapter.normalize_tool_selection(payload)

    engine = PolicyEngine(load_policy_file(Path("rules/tool_file_access.yaml")))
    result = engine.evaluate(
        EvaluationContext(
            stage="tool",
            tool_name=tool_call.tool_name,
            tool_payload=tool_call.arguments,
            provider="llamaindex",
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
