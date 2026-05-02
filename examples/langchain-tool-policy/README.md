# LangChain Tool Policy Example

This example uses a LangChain-style tool object with `name` and `invoke`
attributes. Jinguzhou checks policy before the tool executes.

Run from the repository root:

```bash
PYTHONPATH=src python3 examples/langchain-tool-policy/demo.py
```

Expected output:

```json
{"blocked": true, "called": false, "rule_id": "tool.file.system_write.block"}
```
