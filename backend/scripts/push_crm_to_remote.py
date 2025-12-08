import os
import sys
from typing import Dict

import requests

# Add backend package to path so we can import app.* modules when running as a script
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models import Client, ClientBeneficiary


REMOTE_BASE_URL = os.getenv("REMOTE_BASE_URL")


def _normalize_base_url(base_url: str) -> str:
    base_url = (base_url or "").strip()
    if base_url.endswith("/"):
        base_url = base_url[:-1]
    return base_url


def _to_hebrew_gender(value: str | None) -> str | None:
    text = (value or "").strip()
    if not text:
        return None

    lowered = text.lower()
    if lowered in {"male", "m"}:
        return "זכר"
    if lowered in {"female", "f"}:
        return "נקבה"

    if text in {"זכר", "נקבה"}:
        return text

    return text


def _to_hebrew_marital_status(value: str | None) -> str | None:
    text = (value or "").strip()
    if not text:
        return None

    lowered = text.lower()
    if lowered in {"single", "unmarried"}:
        return "רווק/ה"
    if lowered == "married":
        return "נשוי/ה"
    if lowered == "divorced":
        return "גרוש/ה"
    if lowered in {"widowed", "widow", "widower"}:
        return "אלמן/ה"

    if text in {"רווק", "רווקה", "נשוי", "נשוי/ה", "נשוי/אה", "גרוש", "גרושה", "אלמן", "אלמנה"}:
        return text

    return text


def _build_beneficiaries_payload(client: Client) -> list[Dict]:
    rows: list[Dict] = []
    beneficiaries = getattr(client, "beneficiaries", None) or []
    # Keep the same ordering convention as the CRM service (by index)
    for b in sorted(beneficiaries, key=lambda x: x.index or 0):
        try:
            birth_date_iso = b.birth_date.isoformat() if b.birth_date else ""
        except Exception:  # pragma: no cover - defensive
            birth_date_iso = ""

        rows.append(
            {
                "id": b.id,
                "index": b.index,
                "firstName": b.first_name or "",
                "lastName": b.last_name or "",
                "idNumber": b.id_number or "",
                "birthDate": birth_date_iso,
                "address": b.address or "",
                "relation": b.relation or "",
                "percentage": float(b.percentage or 0.0),
            }
        )

    return rows


def _build_update_payload(client: Client) -> Dict:
    birth_date_iso: str | None
    if getattr(client, "birth_date", None):
        try:
            birth_date_iso = client.birth_date.isoformat()
        except Exception:  # pragma: no cover - defensive
            birth_date_iso = None
    else:
        birth_date_iso = None

    payload: Dict = {
        "firstName": client.first_name,
        "lastName": client.last_name,
        "email": client.email,
        "phone": client.phone,
        "addressStreet": client.address_street,
        "addressCity": client.address_city,
        "addressPostalCode": client.address_postal_code,
        "birthDate": birth_date_iso,
        "gender": _to_hebrew_gender(getattr(client, "gender", None)),
        "maritalStatus": _to_hebrew_marital_status(getattr(client, "marital_status", None)),
        "birthCountry": client.birth_country,
        "employerName": client.employer_name,
        "employerHp": client.employer_hp,
        "employerAddress": client.employer_address,
        "employerPhone": client.employer_phone,
        "addressHouseNumber": client.address_house_number,
        "addressApartment": client.address_apartment,
    }

    beneficiaries_payload = _build_beneficiaries_payload(client)
    if beneficiaries_payload:
        payload["beneficiaries"] = beneficiaries_payload

    return payload


def main() -> None:
    if not REMOTE_BASE_URL:
        print("Error: REMOTE_BASE_URL environment variable is not set.")
        print("Please set it like: $env:REMOTE_BASE_URL='https://ben-zvi.onrender.com'")
        return

    base_url = _normalize_base_url(REMOTE_BASE_URL)
    clients_url = f"{base_url}/api/v1/crm/clients"

    print(f"Fetching remote clients from {clients_url} ...")
    try:
        resp = requests.get(clients_url, timeout=30)
        resp.raise_for_status()
        remote_clients = resp.json() or []
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Error fetching remote clients: {exc}")
        return

    remote_by_id_number: Dict[str, dict] = {}
    for item in remote_clients:
        id_number = (item.get("idNumber") or "").strip()
        if id_number and id_number not in remote_by_id_number:
            remote_by_id_number[id_number] = item

    print(f"Loaded {len(remote_by_id_number)} remote clients indexed by idNumber.")

    db = SessionLocal()
    try:
        local_clients = db.query(Client).all()
        print(f"Found {len(local_clients)} local clients.")

        created_count = 0
        updated_count = 0

        for client in local_clients:
            id_number = (client.id_number or "").strip()
            if not id_number:
                continue

            update_payload = _build_update_payload(client)

            remote_client = remote_by_id_number.get(id_number)
            if remote_client is not None:
                remote_id = remote_client.get("id")
                if not remote_id:
                    continue
                url = f"{base_url}/api/v1/crm/clients/{remote_id}"
                try:
                    r = requests.put(url, json=update_payload, timeout=30)
                    r.raise_for_status()
                    updated_count += 1
                except Exception as exc:  # pragma: no cover - defensive
                    print(f"Failed to update remote client {id_number} (id={remote_id}): {exc}")
            else:
                # Client does not exist remotely: create basic record first (without beneficiaries),
                # then apply full update payload including beneficiaries.
                create_payload = {
                    "idNumber": id_number,
                    "fullName": client.full_name or id_number,
                    **{
                        k: v
                        for k, v in update_payload.items()
                        if k != "beneficiaries"
                    },
                }
                created_id = None
                try:
                    r = requests.post(clients_url, json=create_payload, timeout=30)
                    r.raise_for_status()
                    created = r.json()
                    created_id = created.get("id") if isinstance(created, dict) else None
                    if created_id is not None:
                        remote_by_id_number[id_number] = created
                    created_count += 1
                except Exception as exc:  # pragma: no cover - defensive
                    print(f"Failed to create remote client {id_number}: {exc}")

                if created_id is not None and update_payload:
                    url = f"{base_url}/api/v1/crm/clients/{created_id}"
                    try:
                        r = requests.put(url, json=update_payload, timeout=30)
                        r.raise_for_status()
                        updated_count += 1
                    except Exception as exc:  # pragma: no cover - defensive
                        print(
                            f"Failed to apply update (including beneficiaries) "
                            f"for newly created remote client {id_number} (id={created_id}): {exc}"
                        )

        print(f"Done. Updated {updated_count} remote clients, created {created_count} new remote clients.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
