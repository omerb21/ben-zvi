from __future__ import annotations

import datetime

from bidi.algorithm import get_display

from app.models import Client


def _contains_hebrew(text: str) -> bool:
    for ch in text:
        if "\u0590" <= ch <= "\u05FF":
            return True
    return False


def _normalize_hebrew_value(value: str) -> str:
    if not isinstance(value, str):
        return value
    return value


def _prepare_hebrew_for_pdf_drawing(value: str) -> str:
    """Convert logical Hebrew to visual order for ReportLab text drawing."""
    if not isinstance(value, str) or not _contains_hebrew(value):
        return value
    return get_display(value, base_dir="R")


def _build_client_address(client: Client) -> str:
    address_parts = []
    if client.address_street:
        address_parts.append(client.address_street)
    if client.address_house_number:
        house = str(client.address_house_number)
        if client.address_apartment:
            apartment = str(client.address_apartment)
            address_parts.append(f"{house}/{apartment}")
        else:
            address_parts.append(house)
    if client.address_city:
        address_parts.append(client.address_city)

    return ", ".join(filter(None, address_parts))


def _build_b1_field_values(client: Client, today: str, full_address: str) -> dict[str, str]:
    return {
        "Today": today,
        "ClientFirstName": client.first_name or "",
        "ClientLastName": client.last_name or "",
        "ClientID": client.id_number or "",
        "ClientAddress": full_address,
    }


def _build_b1_context(client: Client) -> tuple[str, str, dict[str, str]]:
    today = datetime.date.today().strftime("%d/%m/%Y")
    full_address = _build_client_address(client)
    field_values = _build_b1_field_values(client, today, full_address)
    return today, full_address, field_values
