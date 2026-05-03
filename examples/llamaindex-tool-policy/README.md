# LlamaIndex Tool Policy Example

This example wraps a LlamaIndex-style tool object and blocks a system-path write
before execution.

Run from the repository root:

```bash
PYTHONPATH=src python3 examples/llamaindex-tool-policy/demo.py
```

Expected output:

```json
{"action": "block", "rule_id": "tool.file.system_write.block", "tool_name": "filesystem.write"}
```
