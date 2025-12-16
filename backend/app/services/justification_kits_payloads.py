from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from app.models import Client, ExistingProduct, NewProduct
from app.services import justification_kits_payloads_utils as _utils
from app.services import justification_kits_payloads_builders as _builders


def _rb(condition: bool) -> str:
    return _utils._rb(condition)


def _normalize_hebrew_value(value: Any) -> Any:
    if not isinstance(value, str):
        return _utils._normalize_hebrew_value(value)
    # For kits we keep Hebrew text in logical order and let the PDF viewer
    # handle right-to-left layout, without reversing or adding marks.
    return _utils._normalize_hebrew_value(value)


def _normalize_payload(
    payload: Dict[str, Any],
    normalize_value_fn: Callable[[Any], Any],
) -> Dict[str, Any]:
    return _utils._normalize_payload(payload, normalize_value_fn)


def _normalize_hebrew_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return _utils._normalize_hebrew_payload(payload)


def _normalize_hebrew_value_reversed(value: Any) -> Any:
    if not isinstance(value, str):
        return _utils._normalize_hebrew_value_reversed(value)
    if not value:
        return _utils._normalize_hebrew_value_reversed(value)
    return _utils._normalize_hebrew_value_reversed(value)


def _normalize_hebrew_payload_reversed(payload: Dict[str, Any]) -> Dict[str, Any]:
    return _utils._normalize_hebrew_payload_reversed(payload)


def sanitize_filename(filename: str) -> str:
    return _utils.sanitize_filename(filename)


def _fmt_date(dt: Any) -> str:
    return _utils._fmt_date(dt)


def build_common_fields(client: Client) -> Dict[str, Any]:
    return _builders.build_common_fields(client)


def build_fund_fields(new_fund: NewProduct, old_fund: Optional[ExistingProduct] = None) -> Dict[str, Any]:
    return _builders.build_fund_fields(new_fund, old_fund)


def _build_full_payload_with_normalizer(
    client: Client,
    new_fund: NewProduct,
    old_fund: Optional[ExistingProduct],
    normalize_payload_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
) -> Dict[str, Any]:
    return _builders._build_full_payload_with_normalizer(
        client,
        new_fund,
        old_fund,
        normalize_payload_fn,
    )


def build_full_payload(
    client: Client,
    new_fund: NewProduct,
    old_fund: Optional[ExistingProduct] = None,
) -> Dict[str, Any]:
    return _builders.build_full_payload(client, new_fund, old_fund)


def build_full_payload_overlay(
    client: Client,
    new_fund: NewProduct,
    old_fund: Optional[ExistingProduct] = None,
) -> Dict[str, Any]:
    return _builders.build_full_payload_overlay(client, new_fund, old_fund)
