"""Output-stage guard wrapper."""

from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.models import EvaluationContext, EvaluationResult


class OutputGuard:
    """Runs output-stage policy checks."""

    def __init__(self, engine: PolicyEngine) -> None:
        self.engine = engine

    def evaluate(self, text: str, model: str = "", provider: str = "") -> EvaluationResult:
        return self.engine.evaluate(
            EvaluationContext(stage="output", text=text, model=model, provider=provider)
        )
