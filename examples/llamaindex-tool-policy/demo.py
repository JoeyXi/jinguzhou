from __future__ import annotations

import json
from pathlib import Path

from jinguzhou.integrations.llamaindex import (
    JinguzhouLlamaIndexMiddleware,
    ToolPolicyViolation,
    guard_tool,
)
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_file


class DemoLlamaIndexTool:
    name = "filesystem.write"

    def call(self, input, **kwargs):
        return {"path": input["path"], "status": "ok"}


def main() -> None:
    middleware = JinguzhouLlamaIndexMiddleware(
        PolicyEngine(load_policy_file(Path("rules/tool_file_access.yaml")))
    )
    guarded = guard_tool(DemoLlamaIndexTool(), middleware)

    try:
        guarded.call({"path": "/etc/hosts", "content": "demo"})
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
