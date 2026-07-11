"""Helpers for Google Ads fetch record previews."""

from __future__ import annotations

_PREVIEW_LIMIT = 10


def preview_records(records: list[dict[str, object]], limit: int = _PREVIEW_LIMIT) -> list[dict[str, object]]:
    """Return up to `limit` unique rows, most recent dates first."""
    seen: set[tuple[str, str]] = set()
    ordered = sorted(records, key=lambda row: str(row.get("Date", "")), reverse=True)
    preview: list[dict[str, object]] = []
    for row in ordered:
        key = (str(row.get("Campaign type", "")), str(row.get("Date", "")))
        if key in seen:
            continue
        seen.add(key)
        preview.append(row)
        if len(preview) >= limit:
            break
    return preview
