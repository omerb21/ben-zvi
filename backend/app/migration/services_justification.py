from typing import Dict

from sqlalchemy.orm import Session

from app.models import Client, ExistingProduct, FormInstance, NewProduct, SavingProduct
from app.utils.id_normalization import normalize_id_number
from app.migration.legacy_justification import (
    JustClient,
    JustExistingProduct,
    JustFormInstance,
    JustNewProduct,
    JustSavingProduct,
    get_justification_session,
)


def migrate_justification_clients_only(
    db: Session,
    justification_url: str | None = None,
) -> Dict[str, int]:
    """Import or back-fill client personal details from legacy justification DB.

    This helper syncs only the Client records (no products or forms):
    - Matches legacy clients by national_id to unified Client.id_number
    - Creates new Client rows when missing
    - Back-fills missing personal fields (name, email, phone, address, gender, marital_status)
      on existing Client rows without overwriting populated values.
    """

    source_session = get_justification_session(justification_url)
    created_clients = 0
    reused_clients = 0
    updated_clients = 0

    try:
        clients_by_id_number: dict[str, Client] = {}
        for existing in db.query(Client).all():
            key_source = existing.id_number or existing.id_number_raw
            key = normalize_id_number(key_source)
            if not key:
                continue
            if key not in clients_by_id_number:
                clients_by_id_number[key] = existing

        legacy_clients = source_session.query(JustClient).all()

        for legacy_client in legacy_clients:
            raw_id = legacy_client.national_id
            id_number = normalize_id_number(raw_id)
            if not id_number:
                continue

            full_name = (
                ((legacy_client.first_name or "") + " " + (legacy_client.last_name or ""))
                .strip()
                or id_number
            )

            client = clients_by_id_number.get(id_number)

            if client is None:
                client = Client(
                    id_number_raw=raw_id,
                    id_number=id_number,
                    full_name=full_name,
                    first_name=legacy_client.first_name,
                    last_name=legacy_client.last_name,
                    gender=legacy_client.gender,
                    marital_status=legacy_client.marital_status,
                    email=legacy_client.email,
                    phone=legacy_client.phone,
                    address_city=legacy_client.city,
                    address_street=legacy_client.street,
                    address_postal_code=legacy_client.zip_code,
                )
                db.add(client)
                db.flush()
                clients_by_id_number[id_number] = client
                created_clients += 1
            else:
                reused_clients += 1
                changed = False

                if not client.first_name and legacy_client.first_name:
                    client.first_name = legacy_client.first_name
                    changed = True
                if not client.last_name and legacy_client.last_name:
                    client.last_name = legacy_client.last_name
                    changed = True
                if not client.gender and legacy_client.gender:
                    client.gender = legacy_client.gender
                    changed = True
                if not client.marital_status and legacy_client.marital_status:
                    client.marital_status = legacy_client.marital_status
                    changed = True
                if not client.email and legacy_client.email:
                    client.email = legacy_client.email
                    changed = True
                if not client.phone and legacy_client.phone:
                    client.phone = legacy_client.phone
                    changed = True
                if not client.address_city and legacy_client.city:
                    client.address_city = legacy_client.city
                    changed = True
                if not client.address_street and legacy_client.street:
                    client.address_street = legacy_client.street
                    changed = True
                if not client.address_postal_code and legacy_client.zip_code:
                    client.address_postal_code = legacy_client.zip_code
                    changed = True

                # Improve full_name if it is empty or just the ID number
                if (not client.full_name or client.full_name == client.id_number) and (
                    client.first_name or client.last_name
                ):
                    parts = [p for p in [client.first_name, client.last_name] if p]
                    if parts:
                        client.full_name = " ".join(parts)
                        changed = True

                if changed:
                    updated_clients += 1

        db.commit()

        return {
            "created_clients": created_clients,
            "updated_clients": updated_clients,
            "reused_clients": reused_clients,
        }
    finally:
        source_session.close()


def migrate_justification(db: Session, justification_url: str | None = None) -> Dict[str, int]:
    source_session = get_justification_session(justification_url)
    created_clients = 0
    reused_clients = 0
    created_saving_products = 0
    created_existing_products = 0
    created_new_products = 0
    created_form_instances = 0

    try:
        clients_by_id_number: dict[str, Client] = {}
        for client in db.query(Client).all():
            key_source = client.id_number or client.id_number_raw
            key = normalize_id_number(key_source)
            if not key:
                continue
            if key not in clients_by_id_number:
                clients_by_id_number[key] = client

        legacy_to_new_client_id: dict[int, int] = {}

        legacy_clients = source_session.query(JustClient).all()
        for legacy_client in legacy_clients:
            raw_id = legacy_client.national_id
            id_number = normalize_id_number(raw_id)
            if not id_number:
                continue

            full_name = ((legacy_client.first_name or "") + " " + (legacy_client.last_name or "")).strip() or id_number

            client = clients_by_id_number.get(id_number)

            if client is None:
                client = Client(
                    id_number_raw=raw_id,
                    id_number=id_number,
                    full_name=full_name,
                    first_name=legacy_client.first_name,
                    last_name=legacy_client.last_name,
                    gender=legacy_client.gender,
                    marital_status=legacy_client.marital_status,
                    email=legacy_client.email,
                    phone=legacy_client.phone,
                    address_city=legacy_client.city,
                    address_street=legacy_client.street,
                    address_postal_code=legacy_client.zip_code,
                )
                db.add(client)
                db.flush()
                clients_by_id_number[id_number] = client
                created_clients += 1
            else:
                reused_clients += 1

            legacy_to_new_client_id[legacy_client.id] = client.id

        existing_saving_products = db.query(SavingProduct).all()
        saving_index: dict[tuple[str, str, str, str], SavingProduct] = {}
        for sp in existing_saving_products:
            key = (sp.fund_type, sp.company_name, sp.fund_name, sp.fund_code)
            saving_index[key] = sp

        legacy_saving_products = source_session.query(JustSavingProduct).all()
        for legacy_sp in legacy_saving_products:
            key = (
                legacy_sp.fund_type,
                legacy_sp.company_name,
                legacy_sp.fund_name,
                legacy_sp.fund_code,
            )
            if key in saving_index:
                continue

            sp = SavingProduct(
                fund_type=legacy_sp.fund_type,
                company_name=legacy_sp.company_name,
                fund_name=legacy_sp.fund_name,
                fund_code=legacy_sp.fund_code,
                yield_1yr=legacy_sp.yield_1yr,
                yield_3yr=legacy_sp.yield_3yr,
                risk_level=legacy_sp.risk_level,
                guaranteed_return=legacy_sp.guaranteed_return,
            )
            db.add(sp)
            saving_index[key] = sp
            created_saving_products += 1

        existing_existing_products = db.query(ExistingProduct).all()
        existing_by_personal_number: dict[str, ExistingProduct] = {}
        for ep in existing_existing_products:
            if ep.personal_number:
                existing_by_personal_number[ep.personal_number] = ep

        legacy_existing_to_new: dict[int, int] = {}

        legacy_existing_products = source_session.query(JustExistingProduct).all()
        for legacy_ep in legacy_existing_products:
            personal_number = legacy_ep.personal_number
            if personal_number and personal_number in existing_by_personal_number:
                existing = existing_by_personal_number[personal_number]
                legacy_existing_to_new[legacy_ep.id] = existing.id
                continue

            client_id = legacy_to_new_client_id.get(legacy_ep.client_id)
            if client_id is None:
                continue

            ep = ExistingProduct(
                client_id=client_id,
                fund_type=legacy_ep.fund_type,
                company_name=legacy_ep.company_name,
                fund_name=legacy_ep.fund_name,
                fund_code=legacy_ep.fund_code,
                yield_1yr=legacy_ep.yield_1yr,
                yield_3yr=legacy_ep.yield_3yr,
                personal_number=legacy_ep.personal_number,
                management_fee_balance=legacy_ep.management_fee_balance,
                management_fee_contributions=legacy_ep.management_fee_contributions,
                accumulated_amount=legacy_ep.accumulated_amount,
                employment_status=legacy_ep.employment_status,
                has_regular_contributions=legacy_ep.has_regular_contributions,
            )
            db.add(ep)
            db.flush()

            if ep.personal_number:
                existing_by_personal_number[ep.personal_number] = ep

            legacy_existing_to_new[legacy_ep.id] = ep.id
            created_existing_products += 1

        existing_new_products = db.query(NewProduct).all()
        new_by_personal_number: dict[str, NewProduct] = {}
        for np in existing_new_products:
            if np.personal_number:
                new_by_personal_number[np.personal_number] = np

        legacy_new_to_new: dict[int, int] = {}

        legacy_new_products = source_session.query(JustNewProduct).all()
        for legacy_np in legacy_new_products:
            personal_number = legacy_np.personal_number
            if personal_number and personal_number in new_by_personal_number:
                existing_np = new_by_personal_number[personal_number]
                legacy_new_to_new[legacy_np.id] = existing_np.id
                continue

            client_id = legacy_to_new_client_id.get(legacy_np.client_id)
            if client_id is None:
                continue

            existing_product_id = None
            if legacy_np.existing_product_id is not None:
                existing_product_id = legacy_existing_to_new.get(legacy_np.existing_product_id)

            np = NewProduct(
                client_id=client_id,
                existing_product_id=existing_product_id,
                fund_type=legacy_np.fund_type,
                company_name=legacy_np.company_name,
                fund_name=legacy_np.fund_name,
                fund_code=legacy_np.fund_code,
                yield_1yr=legacy_np.yield_1yr,
                yield_3yr=legacy_np.yield_3yr,
                personal_number=legacy_np.personal_number,
                management_fee_balance=legacy_np.management_fee_balance,
                management_fee_contributions=legacy_np.management_fee_contributions,
                accumulated_amount=legacy_np.accumulated_amount,
                employment_status=legacy_np.employment_status,
                has_regular_contributions=legacy_np.has_regular_contributions,
            )
            db.add(np)
            db.flush()

            if np.personal_number:
                new_by_personal_number[np.personal_number] = np

            legacy_new_to_new[legacy_np.id] = np.id
            created_new_products += 1

        legacy_form_instances = source_session.query(JustFormInstance).all()
        for legacy_fi in legacy_form_instances:
            new_product_id = legacy_new_to_new.get(legacy_fi.new_product_id)
            if new_product_id is None:
                continue

            fi = FormInstance(
                new_product_id=new_product_id,
                template_filename=legacy_fi.template_filename,
                generated_at=legacy_fi.generated_at,
                status=legacy_fi.status,
                filled_data=legacy_fi.filled_data,
                file_output_path=legacy_fi.file_output_path,
            )
            db.add(fi)
            created_form_instances += 1

        db.commit()

        return {
            "created_clients": created_clients,
            "reused_clients": reused_clients,
            "created_saving_products": created_saving_products,
            "created_existing_products": created_existing_products,
            "created_new_products": created_new_products,
            "created_form_instances": created_form_instances,
        }
    finally:
        source_session.close()
