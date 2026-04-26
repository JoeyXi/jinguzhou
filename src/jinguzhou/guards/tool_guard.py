"""Tool guard helpers."""

from typing import Any, Optional

from jinguzhou.policy.engine import PolicyEngine
from jinguzhou.policy.models import EvaluationContext, EvaluationResult, ToolExtractionConfig


class ToolGuard:
    """Runs tool-stage policy checks."""

    def __init__(self, engine: PolicyEngine) -> None:
        self.engine = engine

    def evaluate(
        self,
        tool_name: str,
        payload: Any,
        model: str = "",
        provider: str = "",
        extraction: Optional[ToolExtractionConfig] = None,
    ) -> EvaluationResult:
        return self.engine.evaluate(
            EvaluationContext(
                stage="tool",
                tool_name=tool_name,
                tool_payload=payload,
                model=model,
                provider=provider,
                tool_extraction=extraction or ToolExtractionConfig(),
            )
        )
