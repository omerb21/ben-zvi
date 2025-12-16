from __future__ import annotations

from typing import Any, Callable, Dict

from app.services.justification_b1 import _contains_hebrew


def _rb(condition: bool) -> str:
    return "/Yes" if condition else "/Off"


def _normalize_hebrew_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    return value


def _normalize_payload(
    payload: Dict[str, Any],
    normalize_value_fn: Callable[[Any], Any],
) -> Dict[str, Any]:
    for key, val in list(payload.items()):
        payload[key] = normalize_value_fn(val)
    return payload


def _normalize_hebrew_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return _normalize_payload(payload, _normalize_hebrew_value)


def _normalize_hebrew_value_reversed(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    if not value:
        return value
    if _contains_hebrew(value):
        return value[::-1]
    return value


def _normalize_hebrew_payload_reversed(payload: Dict[str, Any]) -> Dict[str, Any]:
    return _normalize_payload(payload, _normalize_hebrew_value_reversed)


def sanitize_filename(filename: str) -> str:
    invalid_chars = '<>:"\\/|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    return filename.strip(". ")


def _fmt_date(dt: Any) -> str:
    if not dt:
        return ""
    try:
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return str(dt)
