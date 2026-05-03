# OpenAI Agents Tool Policy Example

This example wraps an OpenAI Agents-style tool callable and blocks destructive
SQL before execution.

Run from the repository root:

```bash
PYTHONPATH=src python3 examples/openai-agents-tool-policy/demo.py
```

Expected output:

```json
{"action": "block", "rule_id": "tool.database.destructive_operation.block", "tool_name": "database.query"}
```
