# OpenAI Agents Tool Policy Example

This example normalizes an OpenAI Agents-style `function_call` output item and
evaluates it with the Jinguzhou database policy pack.

Run from the repository root:

```bash
PYTHONPATH=src python3 examples/openai-agents-tool-policy/demo.py
```

Expected output:

```json
{"action": "block", "rule_id": "tool.database.destructive_operation.block", "tool_name": "database.query"}
```
