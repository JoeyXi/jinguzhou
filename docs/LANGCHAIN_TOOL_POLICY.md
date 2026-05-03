# LangChain Tool Policy

Jinguzhou provides a small LangChain-style middleware that checks a tool call
before the wrapped tool executes.

The integration is dependency-light: it does not import LangChain directly. It
wraps objects with common LangChain tool methods such as `invoke`, `ainvoke`,
`run`, or callable behavior.

## Example

```python
from jinguzhou.integrations.langchain import JinguzhouToolMiddleware, guard_tool
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_file

engine = PolicyEngine(load_policy_file("rules/tool_file_access.yaml"))
middleware = JinguzhouToolMiddleware(engine)
guarded_tool = guard_tool(existing_tool, middleware)

result = guarded_tool.invoke({"path": "README.md"})
```

If policy returns `block` or `require_human_review`, the wrapper raises
`ToolPolicyViolation` and the underlying tool is not executed.

If the middleware is configured with an audit logger and approval manager, the
same tool check can:

- write a `policy_decision` audit event
- require a signed approval token for `require_human_review`
- write an `approval` audit event when the token is accepted

## Runnable Example

```bash
PYTHONPATH=src python3 examples/langchain-tool-policy/demo.py
```
