import os
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
