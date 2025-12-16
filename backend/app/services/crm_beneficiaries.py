from datetime import date

from sqlalchemy.orm import Session

from app.models import Client, ClientBeneficiary
from app.services.crm_utils import _parse_iso_date
from app.utils.strings import strip_or_empty as _strip_or_empty


def _build_beneficiary_fields(item) -> tuple[str, str, str, str, str, str, float]:
    first_name = _strip_or_empty(item.firstName)
    last_name = _strip_or_empty(item.lastName)
    id_number = _strip_or_empty(item.idNumber)
    birth_date_text = _strip_or_empty(item.birthDate)
    address = _strip_or_empty(item.address)
    relation = _strip_or_empty(item.relation)
    percentage_value = float(item.percentage or 0.0)
    return (
        first_name,
        last_name,
        id_number,
        birth_date_text,
        address,
        relation,
        percentage_value,
    )


def _is_beneficiary_all_empty(
    first_name: str,
    last_name: str,
    id_number: str,
    birth_date_text: str,
    address: str,
    relation: str,
    percentage_value: float,
) -> bool:
    return not any(
        [
            first_name,
            last_name,
            id_number,
            birth_date_text,
            address,
            relation,
            percentage_value,
        ]
    )


def _apply_beneficiary_values(
    row: ClientBeneficiary,
    *,
    first_name: str,
    last_name: str,
    id_number: str,
    birth_date_value: date,
    address: str,
    relation: str,
    percentage_value: float,
) -> None:
    row.first_name = first_name
    row.last_name = last_name
    row.id_number = id_number
    row.birth_date = birth_date_value
    row.address = address
    row.relation = relation
    row.percentage = percentage_value


def _sync_client_beneficiaries(db: Session, client: Client, beneficiaries) -> None:
    existing = (
        db.query(ClientBeneficiary)
        .filter(ClientBeneficiary.client_id == client.id)
        .all()
    )
    by_index: dict[int, ClientBeneficiary] = {b.index: b for b in existing}

    seen_indexes: set[int] = set()
    new_rows: list[ClientBeneficiary] = []

    for item in beneficiaries:
        idx = int(item.index)
        if idx < 1 or idx > 4:
            continue
        seen_indexes.add(idx)

        (
            first_name,
            last_name,
            id_number,
            birth_date_text,
            address,
            relation,
            percentage_value,
        ) = _build_beneficiary_fields(item)

        all_empty = _is_beneficiary_all_empty(
            first_name,
            last_name,
            id_number,
            birth_date_text,
            address,
            relation,
            percentage_value,
        )
        if all_empty:
            if idx in by_index:
                db.delete(by_index[idx])
            continue

        birth_date_value = _parse_iso_date(birth_date_text)
        if birth_date_value is None:
            continue

        row = by_index.get(idx)
        if row is None:
            row = ClientBeneficiary(
                client_id=client.id,
                index=idx,
                first_name=first_name,
                last_name=last_name,
                id_number=id_number,
                birth_date=birth_date_value,
                address=address,
                relation=relation,
                percentage=percentage_value,
            )
            db.add(row)
        else:
            _apply_beneficiary_values(
                row,
                first_name=first_name,
                last_name=last_name,
                id_number=id_number,
                birth_date_value=birth_date_value,
                address=address,
                relation=relation,
                percentage_value=percentage_value,
            )
        new_rows.append(row)

    # Delete any beneficiaries that were not mentioned at all
    for idx, row in by_index.items():
        if idx not in seen_indexes:
            db.delete(row)
