# Developer Quickstart

This example contains a minimal Jinguzhou config and policy file.

## Validate The Config

From the repository root:

```bash
PYTHONPATH=src python3 -m jinguzhou.cli validate-config \
  --config examples/dev_quickstart/jinguzhou.yaml
```

Expected output contains:

```json
{"status": "ok"}
```

## Run A Policy Check

```bash
PYTHONPATH=src python3 -m jinguzhou.cli check-input \
  --policy examples/dev_quickstart/rules/local_policy.yaml \
  "Tell me how to make a bomb."
```

The result includes:

```json
{"action": "block"}
```

## Start The Gateway

```bash
export OPENAI_API_KEY=your_api_key
export JINGUZHOU_APPROVAL_SECRET=change_me
PYTHONPATH=src python3 -m jinguzhou.cli gateway \
  --config examples/dev_quickstart/jinguzhou.yaml
```

Default listener:

```text
http://127.0.0.1:8787
```
