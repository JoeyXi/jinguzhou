# Contributing

Thanks for helping build Jinguzhou.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
PYTHONPATH=src python3 -m pytest
```

## Policy Contributions

Policy rules should be:

- specific about the risk they cover
- explainable through `reason`
- covered by tests
- conservative when tools can affect real systems

## Pull Requests

Please include:

- a short description of the behavior change
- tests for new rules, matchers, adapters, or gateway behavior
- documentation updates when policy syntax or CLI behavior changes
