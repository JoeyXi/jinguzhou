import os
import json
import subprocess
import sys


def test_validation_examples_run_successfully() -> None:
    result = subprocess.run(
        [sys.executable, "examples/validation/run_validation.py"],
        check=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": "src"},
        text=True,
    )

    assert '{"examples": 5, "status": "ok"}' in result.stdout


def test_dev_quickstart_config_validates() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "jinguzhou.cli",
            "validate-config",
            "--config",
            "examples/dev_quickstart/jinguzhou.yaml",
        ],
        check=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": "src"},
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["policy_name"] == "dev-quickstart"
    assert payload["rules"] == 2
