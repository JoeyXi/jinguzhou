"""Gateway request and response schemas."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class GatewayError(BaseModel):
    """Structured gateway error."""

    code: str = Field(..., description="Machine-readable error code.")
    message: str = Field(..., description="Human-readable error message.")
    details: dict[str, Any] = Field(default_factory=dict, description="Optional structured details.")


class GatewaySafetyResult(BaseModel):
    """Safety decision details returned for blocked or reviewed requests."""

    request_id: str = Field(..., description="Trace identifier for the request.")
    stage: str = Field(..., description="Safety decision stage.")
    action: str = Field(..., description="Final safety action.")
    policy_name: str = Field(..., description="Evaluated policy name.")
    matched_rule_ids: list[str] = Field(default_factory=list)
    summary: str = Field(..., description="Human-readable decision summary.")
    approval: dict[str, Any] = Field(default_factory=dict)


class GatewayErrorResponse(BaseModel):
    """Structured error response for gateway failures."""

    error: GatewayError
    safety: Optional[GatewaySafetyResult] = None
