# OpenAI Agents Tool Policy

Jinguzhou provides a lightweight OpenAI Agents-style adapter for normalizing
`function_call` output items before a tool executor runs them.

The helper does not import the OpenAI Agents SDK directly. It accepts function
call payloads and maps them into the shared `NormalizedToolCall` model.

## Example

```python
from jinguzhou.adapters.openai_agents import (
    OpenAIAgentsToolAdapter,
    build_openai_agents_function_call,
)

adapter = OpenAIAgentsToolAdapter()
item = build_openai_agents_function_call(
    "db.run_sql",
    {"sql": "DROP TABLE users"},
)
tool_call = adapter.normalize_response_item(item)
```

## Runnable Example

```bash
PYTHONPATH=src python3 examples/openai-agents-tool-policy/demo.py
```
