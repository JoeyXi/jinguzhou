"""Policy evaluation engine."""

from __future__ import annotations

from jinguzhou.policy.matchers import matches
from jinguzhou.policy.models import EvaluationContext, EvaluationResult, PolicyDocument, RuleMatch

ACTION_ORDER = {
    "allow": 0,
    "warn": 1,
    "redact": 2,
    "require_human_review": 3,
    "block": 4,
}

SEVERITY_ORDER = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


class PolicyEngine:
    """Evaluate a normalized context against a policy document."""

    def __init__(self, policy: PolicyDocument) -> None:
        self.policy = policy

    def evaluate(self, context: EvaluationContext) -> EvaluationResult:
        """Evaluate the context and return the strongest matched decision."""
        matched_rules = [
            RuleMatch(
                rule_id=rule.id,
                action=rule.action,
                category=rule.category,
                severity=rule.severity,
                reason=rule.reason,
                priority=rule.priority,
            )
            for rule in self.policy.rules
            if rule.stage == context.stage and matches(context, rule.match)
        ]

        if not matched_rules:
            return EvaluationResult(
                action="allow",
                matched_rules=[],
                policy_name=self.policy.name,
                summary="No rules matched.",
            )

        ranked = sorted(
            matched_rules,
            key=lambda item: (
                ACTION_ORDER[item.action],
                item.priority,
                SEVERITY_ORDER[item.severity],
                item.rule_id,
            ),
            reverse=True,
        )
        final = ranked[0]
        return EvaluationResult(
            action=final.action,
            matched_rules=ranked,
            policy_name=self.policy.name,
            summary=final.reason,
        )
