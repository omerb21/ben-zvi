from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, Optional

import pytz

from app.models import Client, ExistingProduct, NewProduct
from app.services import justification_kits_payloads_builders_helpers as _helpers
from app.services import justification_kits_payloads_utils as _utils


def build_common_fields(client: Client) -> Dict[str, Any]:
    return _helpers.build_common_fields(client)


def build_fund_fields(new_fund: NewProduct, old_fund: Optional[ExistingProduct] = None) -> Dict[str, Any]:
    return _helpers.build_fund_fields(new_fund, old_fund)


def _build_full_payload_with_normalizer(
    client: Client,
    new_fund: NewProduct,
    old_fund: Optional[ExistingProduct],
    normalize_payload_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
) -> Dict[str, Any]:
    return _helpers._build_full_payload_with_normalizer(
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
    return _helpers.build_full_payload(client, new_fund, old_fund)


def build_full_payload_overlay(
    client: Client,
    new_fund: NewProduct,
    old_fund: Optional[ExistingProduct] = None,
) -> Dict[str, Any]:
    return _helpers.build_full_payload_overlay(client, new_fund, old_fund)
