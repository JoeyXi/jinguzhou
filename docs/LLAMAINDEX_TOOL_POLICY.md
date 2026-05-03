# LlamaIndex Tool Policy

Jinguzhou provides a lightweight LlamaIndex-style middleware wrapper for
checking tool calls before execution.

The helper does not import LlamaIndex directly. It wraps tool-like objects and
uses the shared tool firewall middleware for policy, approval, and audit.

## Example

```python
from jinguzhou.integrations.llamaindex import (
    JinguzhouLlamaIndexMiddleware,
    guard_tool,
)
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_file

middleware = JinguzhouLlamaIndexMiddleware(
    PolicyEngine(load_policy_file("rules/tool_file_access.yaml"))
)
guarded_tool = guard_tool(existing_tool, middleware)
guarded_tool.call({"path": "README.md"})
```

## Runnable Example

```bash
PYTHONPATH=src python3 examples/llamaindex-tool-policy/demo.py
```
