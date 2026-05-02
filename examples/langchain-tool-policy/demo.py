from __future__ import annotations

import json
from pathlib import Path

from jinguzhou.integrations.langchain import (
    JinguzhouToolMiddleware,
    ToolPolicyViolation,
    guard_tool,
)
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_file


class DemoWriteTool:
    name = "filesystem.write"

    def __init__(self) -> None:
        self.called = False

    def invoke(self, input, config=None):
        self.called = True
        return {"status": "wrote", "path": input["path"]}


def main() -> None:
    engine = PolicyEngine(load_policy_file(Path("rules/tool_file_access.yaml")))
    middleware = JinguzhouToolMiddleware(engine)
    tool = DemoWriteTool()
    guarded_tool = guard_tool(tool, middleware)

    try:
        guarded_tool.invoke({"path": "/etc/hosts", "content": "demo"})
    except ToolPolicyViolation as exc:
        print(
            json.dumps(
                {
                    "blocked": True,
                    "called": tool.called,
                    "rule_id": exc.result.matched_rules[0].rule_id,
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
