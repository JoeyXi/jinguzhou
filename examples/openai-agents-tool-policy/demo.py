from __future__ import annotations

import json
from pathlib import Path

from jinguzhou.integrations.openai_agents import (
    JinguzhouOpenAIAgentsMiddleware,
    ToolPolicyViolation,
    guard_function_tool,
)
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_file


def main() -> None:
    middleware = JinguzhouOpenAIAgentsMiddleware(
        PolicyEngine(load_policy_file(Path("rules/tool_database_access.yaml")))
    )
    guarded = guard_function_tool(
        "db.run_sql",
        lambda arguments: {"sql": arguments["sql"], "status": "executed"},
        middleware,
    )

    try:
        guarded({"sql": "DROP TABLE users"})
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
