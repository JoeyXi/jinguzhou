"""Release validation runner for Jinguzhou.

Run from the repository root:

    PYTHONPATH=src python3 scripts/validate_release.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], *, env_prefix: dict[str, str] | None = None) -> str:
    env = None
    if env_prefix:
        import os

        env = os.environ.copy()
        env.update(env_prefix)
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> None:
    python = sys.executable
    env = {"PYTHONPATH": "src", "PYTHONPYCACHEPREFIX": "/tmp/jinguzhou-pycache"}
    results = []

    run([python, "-m", "pytest"], env_prefix=env)
    results.append("pytest")

    run([python, "-m", "compileall", "src"], env_prefix=env)
    results.append("compileall")

    version = run([python, "-m", "jinguzhou.cli", "version"], env_prefix=env)
    if version != "0.2.0":
        raise AssertionError(f"Unexpected version: {version}")
    results.append("version")

    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = Path(tmp_dir) / "jinguzhou.yaml"
        init_output = run(
            [
                python,
                "-m",
                "jinguzhou.cli",
                "init",
                "--output",
                str(config_path),
            ],
            env_prefix=env,
        )
        if json.loads(init_output)["status"] != "ok":
            raise AssertionError("Project initialization failed.")
        results.append("init")

        validation = run(
            [
                python,
                "-m",
                "jinguzhou.cli",
                "validate-config",
                "--config",
                str(config_path),
            ],
            env_prefix=env,
        )
        validation_payload = json.loads(validation)
        if validation_payload["status"] != "ok" or validation_payload["rules"] < 1:
            raise AssertionError("Generated config did not validate.")
        results.append("validate_config")

    examples = run([python, "examples/validation/run_validation.py"], env_prefix=env)
    if '{"examples": 5, "status": "ok"}' not in examples:
        raise AssertionError("Validation examples did not complete successfully.")
    results.append("validation_examples")

    blocked = run(
        [
            python,
            "-m",
            "jinguzhou.cli",
            "check-tool",
            "filesystem.write",
            "--policy",
            "rules/tool_use.yaml",
            "--payload",
            '{"path":"/etc/hosts","content":"demo"}',
        ],
        env_prefix=env,
    )
    if json.loads(blocked)["action"] != "block":
        raise AssertionError("filesystem.write /etc/hosts should be blocked.")
    results.append("cli_tool_block")

    print(json.dumps({"status": "ok", "validated": results}, sort_keys=True))


if __name__ == "__main__":
    main()
