"""Input-stage guard wrapper."""

from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.models import EvaluationContext, EvaluationResult


class InputGuard:
    """Runs input-stage policy checks."""

    def __init__(self, engine: PolicyEngine) -> None:
        self.engine = engine

    def evaluate(self, text: str, model: str = "", provider: str = "") -> EvaluationResult:
        return self.engine.evaluate(
            EvaluationContext(stage="input", text=text, model=model, provider=provider)
        )
