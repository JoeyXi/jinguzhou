# LlamaIndex Tool Policy Example

This example normalizes a LlamaIndex-style tool selection payload and evaluates
it with the Jinguzhou file policy pack.

Run from the repository root:

```bash
PYTHONPATH=src python3 examples/llamaindex-tool-policy/demo.py
```

Expected output:

```json
{"action": "block", "rule_id": "tool.file.system_write.block", "tool_name": "filesystem.write"}
```
