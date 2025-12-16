from __future__ import annotations

from typing import Any, Dict, List

import requests


def _normalize_base_url(base_url: str) -> str:
    base_url = (base_url or "").strip()
    if base_url.endswith("/"):
        base_url = base_url[:-1]
    return base_url


def _get_json(url: str) -> Any:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def _safe_get_json(url: str) -> Any:
    try:
        return _get_json(url)
    except Exception:
        return None


def _safe_get_json_list(url: str) -> List[Dict[str, Any]]:
    return _safe_get_json(url) or []


def _build_client_resource_urls(base_url: str, remote_client_id: int) -> tuple[str, str, str]:
    snapshots_url = f"{base_url}/api/v1/crm/clients/{remote_client_id}/snapshots"
    existing_url = f"{base_url}/api/v1/justification/clients/{remote_client_id}/existing-products"
    new_products_url = f"{base_url}/api/v1/justification/clients/{remote_client_id}/new-products"
    return snapshots_url, existing_url, new_products_url


def _fetch_remote_client_payloads(
    base_url: str,
    remote_client_id: int,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    snapshots_url, existing_url, new_products_url = _build_client_resource_urls(base_url, remote_client_id)
    remote_snapshots = _safe_get_json_list(snapshots_url)
    remote_existing = _safe_get_json_list(existing_url)
    remote_new = _safe_get_json_list(new_products_url)
    return remote_snapshots, remote_existing, remote_new
