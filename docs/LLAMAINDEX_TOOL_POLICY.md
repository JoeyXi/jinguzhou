# LlamaIndex Tool Policy

Jinguzhou provides a lightweight LlamaIndex-style adapter for normalizing tool
selection payloads before execution.

The helper does not import LlamaIndex directly. It accepts the common payload
shape of a framework name plus top-level `tool_calls`, then maps the selected
tool into the shared `NormalizedToolCall` model.

## Example

```python
from jinguzhou.adapters.llamaindex import (
    LlamaIndexToolAdapter,
    build_llamaindex_tool_call,
)

adapter = LlamaIndexToolAdapter()
payload = build_llamaindex_tool_call(
    "filesystem.write",
    {"path": "/etc/hosts", "content": "demo"},
)
tool_call = adapter.normalize_tool_selection(payload)
```

## Runnable Example

```bash
PYTHONPATH=src python3 examples/llamaindex-tool-policy/demo.py
```
