from __future__ import annotations

from typing import Any


def strip_or_empty(value: Any) -> str:
    return (value or "").strip()


def coerce_stripped(value: Any) -> str:
    return str(value or "").strip()


def coerce_stripped_or_none(value: Any) -> str | None:
    text = coerce_stripped(value)
    return text or None
