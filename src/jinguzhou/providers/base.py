"""Base provider abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping, Optional


class ProviderAdapter(ABC):
    """Abstract provider adapter interface."""

    @abstractmethod
    async def chat_completions(
        self,
        payload: dict[str, Any],
        *,
        request_id: str = "",
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> dict[str, Any]:
        """Forward a normalized chat completion request."""


class ProviderError(Exception):
    """Structured provider failure raised by adapters."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 502,
        code: str = "provider_error",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}
