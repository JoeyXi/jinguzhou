# Validation Examples

These examples exercise the first-preview release without calling a real LLM
provider.

Run from the repository root:

```bash
PYTHONPATH=src python3 examples/validation/run_validation.py
```

The script validates:

- harmful input policy blocking
- nested JSONPath-like tool payload extraction
- gateway tool-call blocking
- signed approval token retry flow
- audit query and replay

Expected final line:

```json
{"examples": 5, "status": "ok"}
```
