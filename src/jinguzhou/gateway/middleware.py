"""Shared tool firewall middleware with audit and approval hooks."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable, Optional
from uuid import uuid4

from jinguzhou.approvals.tokens import ApprovalClaims, ApprovalTokenManager
from jinguzhou.audit.events import AuditEvent
from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.models import EvaluationContext, EvaluationResult
from jinguzhou.tools.adapters import NormalizedToolCall, ToolAdapterRegistry


BLOCKING_ACTIONS = {"block", "require_human_review"}


def _stringify_metadata(metadata: dict[str, Any]) -> dict[str, str]:
    return {str(key): str(value) for key, value in metadata.items()}


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


def _tool_call_metadata(tool_call: NormalizedToolCall) -> dict[str, Any]:
    payload = tool_call.arguments
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


def _write_audit_event(
    audit_logger: Optional[Any],
    *,
    request_id: str,
    event_type: str,
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
            stage="tool",
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


@dataclass
class ToolFirewallDecision:
    """Result of a middleware tool check."""

    request_id: str
    tool_call: NormalizedToolCall
    result: EvaluationResult
    approval_claims: Optional[ApprovalClaims] = None

    @property
    def approved(self) -> bool:
        return self.approval_claims is not None


class ToolPolicyViolation(RuntimeError):
    """Raised when tool middleware blocks or pauses execution."""

    def __init__(
        self,
        decision: ToolFirewallDecision,
        *,
        approval_enabled: bool = False,
        approval_error: str = "",
    ) -> None:
        self.decision = decision
        self.result = decision.result
        self.tool_call = decision.tool_call
        self.request_id = decision.request_id
        self.approval_enabled = approval_enabled
        self.approval_required = self.result.action == "require_human_review"
        self.approval_error = approval_error

        message = self.result.summary
        if self.approval_required:
            message = f"{message} (request_id={self.request_id})"
        if approval_error:
            message = f"{message} [{approval_error}]"
        super().__init__(message)


class ToolFirewallMiddleware:
    """Shared execution-layer guard for tool middleware integrations."""

    def __init__(
        self,
        policy_engine: PolicyEngine,
        *,
        registry: Optional[ToolAdapterRegistry] = None,
        audit_logger: Optional[Any] = None,
        approval_manager: Optional[ApprovalTokenManager] = None,
        model: str = "",
        provider: str = "",
        framework: str = "",
    ) -> None:
        self.policy_engine = policy_engine
        self.registry = registry or ToolAdapterRegistry.with_defaults()
        self.audit_logger = audit_logger
        self.approval_manager = approval_manager
        self.model = model
        self.provider = provider or framework
        self.framework = framework

    def normalize_tool_call(
        self,
        *,
        protocol: str,
        tool_name: str,
        arguments: Any,
        call_id: str = "",
        type: str = "tool_call",
        raw_payload: Any = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> NormalizedToolCall:
        merged_metadata = dict(metadata or {})
        if self.framework and "framework" not in merged_metadata:
            merged_metadata["framework"] = self.framework
        return self.registry.normalize_tool_call(
            protocol=protocol,
            tool_name=tool_name,
            arguments=arguments,
            id=call_id,
            type=type,
            raw_payload=raw_payload,
            metadata=merged_metadata,
        )

    def evaluate_tool_call(
        self,
        tool_call: NormalizedToolCall,
        *,
        request_id: str = "",
        approval_token: str = "",
        metadata: Optional[dict[str, Any]] = None,
    ) -> ToolFirewallDecision:
        request_id = request_id or str(uuid4())
        runtime_metadata = dict(tool_call.metadata)
        runtime_metadata.update(metadata or {})
        context = EvaluationContext(
            stage="tool",
            tool_name=tool_call.tool_name,
            tool_payload=tool_call.arguments,
            model=self.model,
            provider=self.provider,
            metadata=_stringify_metadata(runtime_metadata),
            tool_extraction=tool_call.extraction,
        )
        result = self.policy_engine.evaluate(context)
        decision = ToolFirewallDecision(
            request_id=request_id,
            tool_call=tool_call,
            result=result,
        )

        audit_metadata = _tool_call_metadata(tool_call)
        audit_metadata.update(runtime_metadata)
        _write_audit_event(
            self.audit_logger,
            request_id=request_id,
            event_type="policy_decision",
            decision=result.action,
            policy_name=result.policy_name,
            matched_rule_ids=_rule_ids(result),
            category=_result_category(result),
            severity=_result_severity(result),
            provider=self.provider,
            model=self.model,
            message=result.summary,
            metadata=audit_metadata,
        )

        if result.action == "require_human_review":
            claims, approval_error = self._approve(
                approval_token,
                request_id=request_id,
                result=result,
                metadata=audit_metadata,
            )
            if claims is None:
                raise ToolPolicyViolation(
                    decision,
                    approval_enabled=self.approval_manager is not None,
                    approval_error=approval_error,
                )
            decision.approval_claims = claims
            _write_audit_event(
                self.audit_logger,
                request_id=request_id,
                event_type="approval",
                decision="approved",
                policy_name=result.policy_name,
                matched_rule_ids=_rule_ids(result),
                category=_result_category(result),
                severity=_result_severity(result),
                provider=self.provider,
                model=self.model,
                message="Human approval token accepted.",
                metadata={
                    **audit_metadata,
                    "approval_id": claims.approval_id,
                    "approver": claims.approver,
                },
            )
            return decision

        if result.action == "block":
            raise ToolPolicyViolation(decision)

        return decision

    def invoke(
        self,
        tool_call: NormalizedToolCall,
        execute: Callable[[Any], Any],
        *,
        request_id: str = "",
        approval_token: str = "",
        metadata: Optional[dict[str, Any]] = None,
    ) -> Any:
        self.evaluate_tool_call(
            tool_call,
            request_id=request_id,
            approval_token=approval_token,
            metadata=metadata,
        )
        return execute(tool_call.arguments)

    async def ainvoke(
        self,
        tool_call: NormalizedToolCall,
        execute: Callable[[Any], Any],
        *,
        request_id: str = "",
        approval_token: str = "",
        metadata: Optional[dict[str, Any]] = None,
    ) -> Any:
        self.evaluate_tool_call(
            tool_call,
            request_id=request_id,
            approval_token=approval_token,
            metadata=metadata,
        )
        result = execute(tool_call.arguments)
        if inspect.isawaitable(result):
            return await result
        return result

    def _approve(
        self,
        approval_token: str,
        *,
        request_id: str,
        result: EvaluationResult,
        metadata: dict[str, Any],
    ) -> tuple[Optional[ApprovalClaims], str]:
        if self.approval_manager is None:
            return None, "approval token required"
        if not approval_token:
            return None, "approval token required"

        try:
            return (
                self.approval_manager.allows(
                    approval_token,
                    request_id=request_id,
                    stage="tool",
                    rule_ids=_rule_ids(result),
                ),
                "",
            )
        except ValueError as exc:
            _write_audit_event(
                self.audit_logger,
                request_id=request_id,
                event_type="approval",
                decision="rejected",
                policy_name=result.policy_name,
                matched_rule_ids=_rule_ids(result),
                category=_result_category(result),
                severity=_result_severity(result),
                provider=self.provider,
                model=self.model,
                message="Human approval token rejected.",
                metadata={**metadata, "approval_error": str(exc)},
            )
            return None, str(exc)
