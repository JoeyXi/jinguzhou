"""Simple redaction helpers."""

from __future__ import annotations

import re

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]


def redact_text(text: str) -> str:
    """Redact common secret-shaped strings."""
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted

