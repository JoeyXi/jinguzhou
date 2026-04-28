"""CLI entrypoint for Jinguzhou."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

import typer
import uvicorn

from jinguzhou.approvals.tokens import ApprovalTokenManager
from jinguzhou.audit.query import query_audit_events, replay_audit_events
from jinguzhou.config import load_runtime_config
from jinguzhou.gateway.runtime import build_app_from_config
from jinguzhou.init_project import write_starter_project
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.loader import load_policy_files
from jinguzhou.policy.models import EvaluationContext, EvaluationResult

app = typer.Typer(help="Jinguzhou safety gateway and policy tooling.")
audit_app = typer.Typer(help="Audit helpers.")
approval_app = typer.Typer(help="Human approval token helpers.")
app.add_typer(audit_app, name="audit")
app.add_typer(approval_app, name="approval")

OutputFormat = Literal["json", "text"]


def _load_engine(policy_paths: list[Path]) -> PolicyEngine:
    policy = load_policy_files(policy_paths)
    return PolicyEngine(policy=policy)


def _emit_payload(payload: dict[str, Any], output: OutputFormat) -> None:
    """Print a dict as JSON or compact text."""
    if output == "json":
        typer.echo(json.dumps(payload, sort_keys=True))
        return

    for key, value in payload.items():
        if isinstance(value, dict):
            typer.echo(f"{key}:")
            for nested_key, nested_value in value.items():
                typer.echo(f"  {nested_key}: {nested_value}")
        elif isinstance(value, list):
            typer.echo(f"{key}: {', '.join(str(item) for item in value)}")
        else:
            typer.echo(f"{key}: {value}")


def _emit_result(result: EvaluationResult, output: OutputFormat) -> None:
    """Print an evaluation result as JSON or human-readable text."""
    if output == "json":
        typer.echo(result.model_dump_json(indent=2))
        return

    typer.echo(f"action: {result.action}")
    typer.echo(f"policy: {result.policy_name}")
    typer.echo(f"summary: {result.summary}")
    if result.matched_rules:
        typer.echo("matched_rules:")
        for rule in result.matched_rules:
            typer.echo(
                f"  - {rule.rule_id} [{rule.severity}/{rule.category}] -> {rule.action}"
            )


def _config_error_payload(config: Path, exc: Exception) -> dict[str, Any]:
    """Return a stable, helpful config validation error payload."""
    message = str(exc)
    hint = "Check the config path and referenced policy files."
    if isinstance(exc, FileNotFoundError):
        missing = str(exc.filename or "")
        if missing and missing.endswith((".yaml", ".yml")):
            hint = f"File not found: {missing}"
        else:
            hint = "A referenced file was not found."
    elif "Unsupported provider type" in message:
        hint = "Set provider.type to openai-compatible or leave it empty."
    elif "Duplicate rule id" in message:
        hint = "Use unique rule IDs across all loaded policy files."
    elif "At least one policy file" in message:
        hint = "Add at least one entry under policy.files."

    return {
        "status": "error",
        "config": str(config),
        "error_type": exc.__class__.__name__,
        "error": message,
        "hint": hint,
    }


@app.command("init")
def init_project(
    output: Path = typer.Option(
        Path("jinguzhou.yaml"),
        "--output",
        "-o",
        help="Path for the starter runtime config.",
    ),
    rules: bool = typer.Option(
        True,
        "--rules/--no-rules",
        help="Create starter rule pack files next to the config.",
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite existing starter files."),
    output_format: OutputFormat = typer.Option(
        "json",
        "--format",
        help="Output format: json or text.",
    ),
) -> None:
    """Create a starter Jinguzhou project config and local rule packs."""
    try:
        result = write_starter_project(output, include_rules=rules, force=force)
    except FileExistsError as exc:
        raise typer.BadParameter(str(exc)) from exc

    _emit_payload(
        {
            "status": "ok",
            "config": str(result.config_path),
            "rules": [str(path) for path in result.rule_paths],
        },
        output_format,
    )


@app.command("validate-config")
def validate_config(
    config: Path = typer.Option(..., help="Path to a Jinguzhou runtime config YAML file."),
    output_format: OutputFormat = typer.Option(
        "json",
        "--format",
        help="Output format: json or text.",
    ),
) -> None:
    """Validate runtime config, policy files, and gateway wiring."""
    try:
        runtime_config = load_runtime_config(config)
        policy_paths = [config.resolve().parent / path for path in runtime_config.policy.files]
        policy = load_policy_files(policy_paths)
        app_instance = build_app_from_config(runtime_config, config.resolve().parent)
    except Exception as exc:
        _emit_payload(_config_error_payload(config, exc), output_format)
        raise typer.Exit(1) from exc

    _emit_payload(
        {
            "status": "ok",
            "config": str(config),
            "policy_name": policy.name,
            "policy_files": len(policy_paths),
            "rules": len(policy.rules),
            "gateway": {
                "host": runtime_config.gateway.host,
                "port": runtime_config.gateway.port,
            },
            "provider_type": runtime_config.provider.type,
            "audit_enabled": app_instance.state.audit_logger is not None,
            "approval_enabled": app_instance.state.approval_manager is not None,
        },
        output_format,
    )


@app.command("check-input")
def check_input(
    policy: list[Path] = typer.Option(..., help="One or more policy files to load."),
    text: str = typer.Argument(..., help="Input text to evaluate."),
    model: str = "",
    provider: str = "",
    output_format: OutputFormat = typer.Option(
        "json",
        "--format",
        help="Output format: json or text.",
    ),
) -> None:
    """Evaluate an input string against a policy file."""
    engine = _load_engine(policy)
    result = engine.evaluate(
        EvaluationContext(stage="input", text=text, model=model, provider=provider)
    )
    _emit_result(result, output_format)


@app.command("check-output")
def check_output(
    policy: list[Path] = typer.Option(..., help="One or more policy files to load."),
    text: str = typer.Argument(..., help="Output text to evaluate."),
    model: str = "",
    provider: str = "",
    output_format: OutputFormat = typer.Option(
        "json",
        "--format",
        help="Output format: json or text.",
    ),
) -> None:
    """Evaluate an output string against a policy file."""
    engine = _load_engine(policy)
    result = engine.evaluate(
        EvaluationContext(stage="output", text=text, model=model, provider=provider)
    )
    _emit_result(result, output_format)


@app.command("check-tool")
def check_tool(
    tool: str = typer.Argument(..., help="Tool name to evaluate."),
    policy: list[Path] = typer.Option(..., help="One or more policy files to load."),
    payload: str = typer.Option("{}", help="JSON payload for the tool request."),
    model: str = "",
    provider: str = "",
    output_format: OutputFormat = typer.Option(
        "json",
        "--format",
        help="Output format: json or text.",
    ),
) -> None:
    """Evaluate a tool action against a policy file."""
    engine = _load_engine(policy)
    parsed_payload: Any = json.loads(payload)
    result = engine.evaluate(
        EvaluationContext(
            stage="tool",
            tool_name=tool,
            tool_payload=parsed_payload,
            model=model,
            provider=provider,
        )
    )
    _emit_result(result, output_format)


@app.command("gateway")
def gateway(
    config: Path = typer.Option(..., help="Path to a Jinguzhou runtime config YAML file."),
    host: str = typer.Option("", help="Optional host override."),
    port: int = typer.Option(0, help="Optional port override."),
) -> None:
    """Run the Jinguzhou gateway with runtime configuration."""
    runtime_config = load_runtime_config(config)
    app_instance = build_app_from_config(runtime_config, config.resolve().parent)
    listen_host = host or runtime_config.gateway.host
    listen_port = port or runtime_config.gateway.port

    typer.echo(f"Starting Jinguzhou gateway on http://{listen_host}:{listen_port}")
    uvicorn.run(app_instance, host=listen_host, port=listen_port)


@audit_app.command("tail")
def audit_tail(file: Path, lines: int = 20) -> None:
    """Print the last few audit lines."""
    if not file.exists():
        raise typer.BadParameter(f"Audit file not found: {file}")

    content = file.read_text(encoding="utf-8").splitlines()
    for entry in content[-lines:]:
        typer.echo(entry)


@audit_app.command("query")
def audit_query(
    file: Path,
    request_id: str = "",
    stage: str = "",
    decision: str = "",
    rule_id: str = "",
    limit: int = 50,
) -> None:
    """Query audit events and print JSONL results."""
    for event in query_audit_events(
        file,
        request_id=request_id,
        stage=stage,
        decision=decision,
        rule_id=rule_id,
        limit=limit,
    ):
        typer.echo(event.model_dump_json())


@audit_app.command("replay")
def audit_replay(file: Path, request_id: str = "") -> None:
    """Replay a compact audit timeline."""
    for line in replay_audit_events(file, request_id=request_id):
        typer.echo(line)


@approval_app.command("issue")
def approval_issue(
    secret: str = typer.Option(..., help="Shared approval signing secret."),
    request_id: str = typer.Option(..., help="Gateway request ID to approve."),
    stage: str = typer.Option(..., help="Stage to approve: input, output, or tool."),
    rule_id: list[str] = typer.Option(..., help="Rule IDs covered by the approval."),
    approver: str = "",
    reason: str = "",
    ttl_seconds: int = 900,
) -> None:
    """Issue a signed approval token for a pending human-review decision."""
    token = ApprovalTokenManager(secret).issue(
        request_id=request_id,
        stage=stage,
        rule_ids=rule_id,
        approver=approver,
        reason=reason,
        ttl_seconds=ttl_seconds,
    )
    typer.echo(token)


@approval_app.command("decode")
def approval_decode(secret: str, token: str) -> None:
    """Verify and decode an approval token."""
    claims = ApprovalTokenManager(secret).decode(token)
    typer.echo(claims.model_dump_json(indent=2))


@app.command("version")
def version() -> None:
    """Print the current package version."""
    from jinguzhou import __version__

    typer.echo(__version__)


def main() -> None:
    """Run the CLI."""
    app()


if __name__ == "__main__":
    main()
