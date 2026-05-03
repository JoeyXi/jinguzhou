# OpenAI Agents Tool Policy

Jinguzhou provides a lightweight OpenAI Agents-style middleware wrapper for
checking `function_call` executions before a tool runs.

The helper does not import the OpenAI Agents SDK directly. It wraps a callable
tool function and uses the shared tool firewall middleware for policy,
approval, and audit.

## Example

```python
from jinguzhou.integrations.openai_agents import (
    JinguzhouOpenAIAgentsMiddleware,
    guard_function_tool,
)
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_file

middleware = JinguzhouOpenAIAgentsMiddleware(
    PolicyEngine(load_policy_file("rules/tool_database_access.yaml"))
)
guarded_tool = guard_function_tool("db.run_sql", existing_tool, middleware)
guarded_tool({"sql": "SELECT 1"})
```

## Runnable Example

```bash
PYTHONPATH=src python3 examples/openai-agents-tool-policy/demo.py
```
