from __future__ import annotations

import json
from pathlib import Path

from jinguzhou.adapters.openai_agents import (
    OpenAIAgentsToolAdapter,
    build_openai_agents_function_call,
)
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_file
from jinguzhou.policy.models import EvaluationContext


def main() -> None:
    adapter = OpenAIAgentsToolAdapter()
    item = build_openai_agents_function_call(
        "db.run_sql",
        {"sql": "DROP TABLE users"},
        call_id="demo-openai-agents-call",
    )
    tool_call = adapter.normalize_response_item(item)

    engine = PolicyEngine(load_policy_file(Path("rules/tool_database_access.yaml")))
    result = engine.evaluate(
        EvaluationContext(
            stage="tool",
            tool_name=tool_call.tool_name,
            tool_payload=tool_call.arguments,
            provider="openai_agents",
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
