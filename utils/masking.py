"""Secret masking utilities."""

from __future__ import annotations


def mask_secret(value: str | None, visible: int = 4) -> str:
    if not value:
        return "Not configured"
    text = str(value)
    if len(text) <= visible * 2:
        return "*" * len(text)
    return f"{text[:visible]}...{text[-visible:]}"
