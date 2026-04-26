"""OpenAI-compatible provider adapter."""

from __future__ import annotations

from typing import Any, Mapping, Optional

import httpx

from jinguzhou.providers.base import ProviderAdapter, ProviderError


class OpenAICompatibleProvider(ProviderAdapter):
    """Minimal provider wrapper used by the future gateway."""

    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        *,
        timeout_seconds: float = 60.0,
        default_headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.default_headers = dict(default_headers or {})

    async def chat_completions(
        self,
        payload: dict[str, Any],
        *,
        request_id: str = "",
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> dict[str, Any]:
        headers = dict(self.default_headers)
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if request_id:
            headers["x-request-id"] = request_id
        if extra_headers:
            headers.update(extra_headers)

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as exc:
            raise ProviderError(
                "Upstream provider request timed out.",
                status_code=504,
                code="provider_timeout",
                details={"request_id": request_id, "base_url": self.base_url},
            ) from exc
        except httpx.HTTPStatusError as exc:
            response = exc.response
            upstream_text = response.text
            upstream_request_id = response.headers.get("x-request-id", "")
            raise ProviderError(
                "Upstream provider returned an error response.",
                status_code=response.status_code,
                code="provider_http_error",
                details={
                    "request_id": request_id,
                    "upstream_request_id": upstream_request_id,
                    "upstream_body": upstream_text,
                    "base_url": self.base_url,
                },
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(
                "Upstream provider request failed.",
                status_code=502,
                code="provider_transport_error",
                details={"request_id": request_id, "base_url": self.base_url},
            ) from exc
