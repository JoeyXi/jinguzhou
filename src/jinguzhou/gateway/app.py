"""FastAPI gateway implementation."""

from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from jinguzhou import __version__
from jinguzhou.audit.events import AuditEvent
from jinguzhou.audit.logger import JsonlAuditLogger
from jinguzhou.approvals.tokens import ApprovalClaims, ApprovalTokenManager
from jinguzhou.gateway.schemas import GatewayError, GatewayErrorResponse, GatewaySafetyResult
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.models import EvaluationContext, EvaluationResult
from jinguzhou.providers.base import ProviderAdapter, ProviderError
from jinguzhou.tools.adapters import ToolAdapterRegistry, ToolInvocation


def _message_content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return "\n".join(part for part in parts if part)
    return str(content or "")


def _extract_input_text(payload: dict[str, Any]) -> str:
    messages = payload.get("messages", [])
    segments = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role", ""))
        content = _message_content_to_text(message.get("content", ""))
        if content:
            segments.append(f"{role}: {content}".strip())
    return "\n".join(segments)


def _extract_output_text(response_payload: dict[str, Any]) -> str:
    choices = response_payload.get("choices", [])
    segments = []
    for choice in choices:
        if not isinstance(choice, dict):
            continue
        message = choice.get("message", {})
        if isinstance(message, dict):
            content = _message_content_to_text(message.get("content", ""))
            if content:
                segments.append(content)
    return "\n".join(segments)


def _redact_output_text(response_payload: dict[str, Any], replacement: str) -> dict[str, Any]:
    redacted = dict(response_payload)
    choices = list(redacted.get("choices", []))
    if not choices:
        return redacted

    first_choice = dict(choices[0])
    message = dict(first_choice.get("message", {}))
    message["content"] = replacement
    first_choice["message"] = message
    choices[0] = first_choice
    redacted["choices"] = choices
    redacted["jinguzhou"] = {
        "output_action": "redact",
        "message": "Output content was redacted by Jinguzhou policy.",
    }
    return redacted


def _provider_name(provider: Optional[ProviderAdapter]) -> str:
    if provider is None:
        return ""
    return provider.__class__.__name__


def _write_audit_event(
    audit_logger: Optional[JsonlAuditLogger],
    *,
    request_id: str,
    event_type: str,
    stage: str,
    decision: str,
    policy_name: str,
    matched_rule_ids: list[str],
    category: str,
    severity: str,
    provider: str,
    model: str,
    message: str,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    if audit_logger is None:
        return

    audit_logger.write(
        AuditEvent(
            request_id=request_id,
            event_type=event_type,
            stage=stage,
            decision=decision,
            policy_name=policy_name,
            matched_rule_ids=matched_rule_ids,
            category=category,
            severity=severity,
            provider=provider,
            model=model,
            message=message,
            metadata=metadata or {},
        )
    )


def _result_category(result: EvaluationResult) -> str:
    if not result.matched_rules:
        return ""
    return result.matched_rules[0].category


def _result_severity(result: EvaluationResult) -> str:
    if not result.matched_rules:
        return ""
    return result.matched_rules[0].severity


def _rule_ids(result: EvaluationResult) -> list[str]:
    return [rule.rule_id for rule in result.matched_rules]


def _blocked_response(
    request_id: str,
    result: EvaluationResult,
    stage: str,
    *,
    approval_enabled: bool = False,
) -> JSONResponse:
    status_code = 403 if result.action == "block" else 409
    code = "safety_blocked" if result.action == "block" else "human_review_required"
    approval = {}
    if result.action == "require_human_review":
        approval = {
            "enabled": approval_enabled,
            "request_id": request_id,
            "stage": stage,
            "rule_ids": _rule_ids(result),
            "header": "x-jinguzhou-approval-token",
        }
    response = GatewayErrorResponse(
        error=GatewayError(code=code, message=result.summary),
        safety=GatewaySafetyResult(
            request_id=request_id,
            stage=stage,
            action=result.action,
            policy_name=result.policy_name,
            matched_rule_ids=_rule_ids(result),
            summary=result.summary,
            approval=approval,
        ),
    )
    return JSONResponse(status_code=status_code, content=response.model_dump(mode="json"))


def _approval_from_request(
    request: Request,
    manager: Optional[ApprovalTokenManager],
    *,
    request_id: str,
    stage: str,
    result: EvaluationResult,
) -> Optional[ApprovalClaims]:
    if manager is None or result.action != "require_human_review":
        return None
    token = request.headers.get("x-jinguzhou-approval-token", "")
    if not token:
        return None
    try:
        return manager.allows(
            token,
            request_id=request_id,
            stage=stage,
            rule_ids=_rule_ids(result),
        )
    except ValueError:
        return None


def _tool_call_metadata(tool_call: ToolInvocation) -> dict[str, Any]:
    payload = tool_call.tool_payload
    payload_keys = []
    if isinstance(payload, dict):
        payload_keys = sorted(str(key) for key in payload.keys())

    return {
        "tool_call_id": tool_call.id,
        "tool_type": tool_call.type,
        "tool_name": tool_call.tool_name,
        "tool_raw_name": tool_call.raw_tool_name,
        "tool_protocol": tool_call.protocol,
        "tool_adapter": tool_call.adapter_name,
        "tool_payload_keys": payload_keys,
    }


def create_app(
    *,
    policy_engine: Optional[PolicyEngine] = None,
    provider: Optional[ProviderAdapter] = None,
    audit_logger: Optional[JsonlAuditLogger] = None,
    tool_adapter_registry: Optional[ToolAdapterRegistry] = None,
    approval_manager: Optional[ApprovalTokenManager] = None,
) -> FastAPI:
    """Create a FastAPI gateway app with injectable dependencies."""
    app = FastAPI(title="Jinguzhou Gateway", version=__version__)
    app.state.policy_engine = policy_engine
    app.state.provider = provider
    app.state.audit_logger = audit_logger
    app.state.tool_adapter_registry = tool_adapter_registry or ToolAdapterRegistry.with_defaults()
    app.state.approval_manager = approval_manager

    @app.get("/health")
    def health() -> dict[str, str]:
        """Simple health endpoint."""
        return {"status": "ok"}

    @app.get("/version")
    def version() -> dict[str, str]:
        """Gateway version endpoint."""
        return {"version": __version__}

    @app.post("/v1/chat/completions")
    async def chat_completions(payload: dict[str, Any], request: Request) -> Any:
        """Guard and forward chat completions requests."""
        provider_adapter = app.state.provider
        audit = app.state.audit_logger
        engine = app.state.policy_engine
        approval = app.state.approval_manager
        request_id = request.headers.get("x-request-id", str(uuid4()))
        model = str(payload.get("model", ""))
        provider_name = _provider_name(provider_adapter)
        input_text = _extract_input_text(payload)

        if provider_adapter is None:
            response = GatewayErrorResponse(
                error=GatewayError(
                    code="provider_not_configured",
                    message="No provider adapter is configured for the gateway.",
                )
            )
            return JSONResponse(status_code=503, content=response.model_dump(mode="json"))

        if engine is not None:
            input_result = engine.evaluate(
                EvaluationContext(
                    stage="input",
                    text=input_text,
                    model=model,
                    provider=provider_name,
                )
            )
            _write_audit_event(
                audit,
                request_id=request_id,
                event_type="policy_decision",
                stage="input",
                decision=input_result.action,
                policy_name=input_result.policy_name,
                matched_rule_ids=[rule.rule_id for rule in input_result.matched_rules],
                category=_result_category(input_result),
                severity=_result_severity(input_result),
                provider=provider_name,
                model=model,
                message=input_result.summary,
                metadata={"message_count": len(payload.get("messages", []))},
            )
            if input_result.action == "require_human_review":
                claims = _approval_from_request(
                    request,
                    approval,
                    request_id=request_id,
                    stage="input",
                    result=input_result,
                )
                if claims is None:
                    return _blocked_response(
                        request_id,
                        input_result,
                        "input",
                        approval_enabled=approval is not None,
                    )
                _write_audit_event(
                    audit,
                    request_id=request_id,
                    event_type="approval",
                    stage="input",
                    decision="approved",
                    policy_name=input_result.policy_name,
                    matched_rule_ids=_rule_ids(input_result),
                    category=_result_category(input_result),
                    severity=_result_severity(input_result),
                    provider=provider_name,
                    model=model,
                    message="Human approval token accepted.",
                    metadata={"approval_id": claims.approval_id, "approver": claims.approver},
                )
            elif input_result.action == "block":
                return _blocked_response(request_id, input_result, "input")

        try:
            provider_response = await provider_adapter.chat_completions(
                payload,
                request_id=request_id,
            )
        except ProviderError as exc:
            _write_audit_event(
                audit,
                request_id=request_id,
                event_type="gateway_error",
                stage="provider",
                decision="error",
                policy_name="",
                matched_rule_ids=[],
                category="",
                severity="",
                provider=provider_name,
                model=model,
                message=exc.message,
                metadata=exc.details,
            )
            response = GatewayErrorResponse(
                error=GatewayError(
                    code=exc.code,
                    message=exc.message,
                    details=exc.details,
                )
            )
            return JSONResponse(status_code=exc.status_code, content=response.model_dump(mode="json"))
        except Exception as exc:
            _write_audit_event(
                audit,
                request_id=request_id,
                event_type="gateway_error",
                stage="provider",
                decision="error",
                policy_name="",
                matched_rule_ids=[],
                category="",
                severity="",
                provider=provider_name,
                model=model,
                message=str(exc),
            )
            response = GatewayErrorResponse(
                error=GatewayError(
                    code="provider_error",
                    message="Provider request failed.",
                )
            )
            return JSONResponse(status_code=502, content=response.model_dump(mode="json"))

        if engine is None:
            return provider_response

        output_text = _extract_output_text(provider_response)
        output_result = engine.evaluate(
            EvaluationContext(
                stage="output",
                text=output_text,
                model=model,
                provider=provider_name,
            )
        )
        _write_audit_event(
            audit,
            request_id=request_id,
            event_type="policy_decision",
            stage="output",
            decision=output_result.action,
            policy_name=output_result.policy_name,
            matched_rule_ids=[rule.rule_id for rule in output_result.matched_rules],
            category=_result_category(output_result),
            severity=_result_severity(output_result),
            provider=provider_name,
            model=model,
            message=output_result.summary,
            metadata={"choice_count": len(provider_response.get("choices", []))},
        )

        if output_result.action == "require_human_review":
            claims = _approval_from_request(
                request,
                approval,
                request_id=request_id,
                stage="output",
                result=output_result,
            )
            if claims is None:
                return _blocked_response(
                    request_id,
                    output_result,
                    "output",
                    approval_enabled=approval is not None,
                )
            _write_audit_event(
                audit,
                request_id=request_id,
                event_type="approval",
                stage="output",
                decision="approved",
                policy_name=output_result.policy_name,
                matched_rule_ids=_rule_ids(output_result),
                category=_result_category(output_result),
                severity=_result_severity(output_result),
                provider=provider_name,
                model=model,
                message="Human approval token accepted.",
                metadata={"approval_id": claims.approval_id, "approver": claims.approver},
            )
        elif output_result.action == "block":
            return _blocked_response(request_id, output_result, "output")

        if output_result.action == "redact":
            return _redact_output_text(
                provider_response,
                "[REDACTED by Jinguzhou policy]",
            )

        tool_calls = app.state.tool_adapter_registry.extract_tool_calls(provider_response)
        for tool_call in tool_calls:
            tool_result = engine.evaluate(
                EvaluationContext(
                    stage="tool",
                    tool_name=tool_call.tool_name,
                    tool_payload=tool_call.tool_payload,
                    model=model,
                    provider=provider_name,
                    tool_extraction=tool_call.extraction,
                )
            )
            _write_audit_event(
                audit,
                request_id=request_id,
                event_type="policy_decision",
                stage="tool",
                decision=tool_result.action,
                policy_name=tool_result.policy_name,
                matched_rule_ids=[rule.rule_id for rule in tool_result.matched_rules],
                category=_result_category(tool_result),
                severity=_result_severity(tool_result),
                provider=provider_name,
                model=model,
                message=tool_result.summary,
                metadata=_tool_call_metadata(tool_call),
            )
            if tool_result.action == "require_human_review":
                claims = _approval_from_request(
                    request,
                    approval,
                    request_id=request_id,
                    stage="tool",
                    result=tool_result,
                )
                if claims is None:
                    return _blocked_response(
                        request_id,
                        tool_result,
                        "tool",
                        approval_enabled=approval is not None,
                    )
                _write_audit_event(
                    audit,
                    request_id=request_id,
                    event_type="approval",
                    stage="tool",
                    decision="approved",
                    policy_name=tool_result.policy_name,
                    matched_rule_ids=_rule_ids(tool_result),
                    category=_result_category(tool_result),
                    severity=_result_severity(tool_result),
                    provider=provider_name,
                    model=model,
                    message="Human approval token accepted.",
                    metadata={"approval_id": claims.approval_id, "approver": claims.approver},
                )
            elif tool_result.action == "block":
                return _blocked_response(request_id, tool_result, "tool")

        return provider_response

    return app


app = create_app()
