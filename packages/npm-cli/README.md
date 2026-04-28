# @jinguzhou/cli

Thin npm launcher for the Jinguzhou Python CLI.

This package does not reimplement the policy engine. It invokes:

```bash
python3 -m jinguzhou.cli
```

Install the Python package first:

```bash
python3 -m pip install jinguzhou
```

Then run:

```bash
npx @jinguzhou/cli version
npx @jinguzhou/cli init --output jinguzhou.yaml
npx @jinguzhou/cli validate-config --config jinguzhou.yaml
```
