from typing import List, Dict, Any

from sqlalchemy.orm import Session

from app.models import SavingProduct, ExistingProduct, NewProduct, FormInstance, Snapshot
from app.schemas.justification import (
    NewProductCreate,
    FormInstanceCreate,
    ExistingProductCreate,
    ExistingProductUpdate,
)
from app.utils.source_names import get_source_display_name


def list_saving_products(db: Session) -> List[SavingProduct]:
    """Return all saving products ordered by company and fund name."""
    return (
        db.query(SavingProduct)
        .order_by(SavingProduct.company_name, SavingProduct.fund_name)
        .all()
    )


def list_existing_products_for_client(db: Session, client_id: int) -> List[ExistingProduct]:
    """Return all existing products for a specific client."""
    return (
        db.query(ExistingProduct)
        .filter(ExistingProduct.client_id == client_id)
        .order_by(ExistingProduct.company_name, ExistingProduct.fund_name)
        .all()
    )


def create_existing_product_for_client(
    db: Session,
    client_id: int,
    existing_in: ExistingProductCreate,
) -> ExistingProduct:
    """Create a manually-entered existing product for the given client."""

    product = ExistingProduct(
        client_id=client_id,
        fund_type=existing_in.fundType,
        company_name=existing_in.companyName,
        fund_name=existing_in.fundName,
        fund_code=existing_in.fundCode,
        yield_1yr=existing_in.yield1yr,
        yield_3yr=existing_in.yield3yr,
        personal_number=existing_in.personalNumber,
        management_fee_balance=existing_in.managementFeeBalance,
        management_fee_contributions=existing_in.managementFeeContributions,
        accumulated_amount=existing_in.accumulatedAmount,
        employment_status=existing_in.employmentStatus,
        has_regular_contributions=existing_in.hasRegularContributions,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_existing_product(
    db: Session,
    existing_product_id: int,
    existing_in: ExistingProductUpdate,
) -> ExistingProduct | None:
    """Update fields of an existing product by ID.

    Returns the updated product, or None if not found.
    """

    product = (
        db.query(ExistingProduct)
        .filter(ExistingProduct.id == existing_product_id)
        .first()
    )
    if not product:
        return None

    data = existing_in.dict(exclude_unset=True)

    if "fundType" in data:
        product.fund_type = data["fundType"]
    if "companyName" in data:
        product.company_name = data["companyName"]
    if "fundName" in data:
        product.fund_name = data["fundName"]
    if "fundCode" in data:
        product.fund_code = data["fundCode"]
    if "yield1yr" in data:
        product.yield_1yr = data["yield1yr"]
    if "yield3yr" in data:
        product.yield_3yr = data["yield3yr"]
    if "personalNumber" in data:
        product.personal_number = data["personalNumber"]
    if "managementFeeBalance" in data:
        product.management_fee_balance = data["managementFeeBalance"]
    if "managementFeeContributions" in data:
        product.management_fee_contributions = data["managementFeeContributions"]
    if "accumulatedAmount" in data:
        product.accumulated_amount = data["accumulatedAmount"]
    if "employmentStatus" in data:
        product.employment_status = data["employmentStatus"]
    if "hasRegularContributions" in data:
        product.has_regular_contributions = data["hasRegularContributions"]

    db.commit()
    db.refresh(product)
    return product


def list_existing_products_view_for_client(
    db: Session,
    client_id: int,
) -> List[Dict[str, Any]]:
    """Return existing products for justification UI.

    Combines real ExistingProduct rows (manually entered / migrated) with
    virtual products derived from CRM snapshots and saving products.
    """

    # Real existing products from justification DB
    real_products = list_existing_products_for_client(db, client_id)

    items: List[Dict[str, Any]] = []
    # Use a key to avoid duplicating products when we also derive them from snapshots
    seen_keys: set[tuple[str, str, str]] = set()

    for p in real_products:
        key = (
            (p.fund_code or "").strip(),
            (p.fund_name or "").strip(),
            (p.fund_type or "").strip(),
        )
        seen_keys.add(key)
        items.append(
            {
                "id": p.id,
                "client_id": p.client_id,
                "fund_type": p.fund_type or "",
                "company_name": p.company_name or "",
                "fund_name": p.fund_name or "",
                "fund_code": p.fund_code or "",
                "yield_1yr": p.yield_1yr,
                "yield_3yr": p.yield_3yr,
                "personal_number": p.personal_number,
                "management_fee_balance": p.management_fee_balance,
                "management_fee_contributions": p.management_fee_contributions,
                "accumulated_amount": p.accumulated_amount,
                "employment_status": p.employment_status,
                "has_regular_contributions": p.has_regular_contributions,
                "is_virtual": False,
            }
        )

    # Derive additional products from CRM snapshots
    snapshots = (
        db.query(Snapshot)
        .filter(Snapshot.client_id == client_id, Snapshot.is_active.is_(True))
        .all()
    )
    if not snapshots:
        return items

    # For each (fund_code, fund_number) keep the latest snapshot by date
    latest_by_key: Dict[tuple[str, str], Snapshot] = {}
    for s in snapshots:
        fund_code = (s.fund_code or "").strip()
        fund_number = (s.fund_number or "").strip()
        if not fund_code and not fund_number:
            continue
        key = (fund_code, fund_number)
        current = latest_by_key.get(key)
        if current is None or (s.snapshot_date or "") > (current.snapshot_date or ""):
            latest_by_key[key] = s

    if not latest_by_key:
        return items

    # Load all saving products once for code and name+company matching
    saving_products = db.query(SavingProduct).all()
    saving_by_code: Dict[str, SavingProduct] = {}
    for sp in saving_products:
        code = (sp.fund_code or "").strip()
        if code and code not in saving_by_code:
            saving_by_code[code] = sp

    virtual_id = -1
    for (fund_code, fund_number), snap in latest_by_key.items():
        key = (
            (fund_code or "").strip(),
            (snap.fund_name or "").strip(),
            (snap.fund_type or "").strip(),
        )
        if key in seen_keys:
            continue

        # Try to resolve the product from the market table (SavingProduct)
        # 1. Prefer match by fund name + company (derived from source), as in the old system
        sp = None
        if snap.fund_name and snap.source:
            expected_company = get_source_display_name(snap.source or "") or ""
            fund_name_raw = (snap.fund_name or "").strip()

            def _norm_company(value: str) -> str:
                return "".join(
                    ch for ch in value.strip().lower() if not ch.isspace() and ch not in {"-", "'", '"'}
                )

            expected_norm = _norm_company(expected_company)
            for candidate in saving_products:
                if (candidate.fund_name or "").strip() != fund_name_raw:
                    continue
                cand_norm = _norm_company(candidate.company_name or "")
                if not cand_norm or not expected_norm:
                    continue
                if cand_norm.startswith(expected_norm) or expected_norm.startswith(cand_norm):
                    sp = candidate
                    break

        # 2. Fallback: try to match by fund code if we still did not find a product
        if sp is None:
            clean_code = (fund_code or "").strip()
            if clean_code:
                sp = saving_by_code.get(clean_code)

        fund_type = (snap.fund_type or (sp.fund_type if sp else "")) or ""
        fund_name = (snap.fund_name or (sp.fund_name if sp else "")) or ""
        company_name = (sp.company_name if sp else get_source_display_name(snap.source or "")) or ""

        if not fund_name and not company_name and not fund_type:
            # Not enough information to show a meaningful product
            continue

        personal_number = fund_number or fund_code or f"CRM-{client_id}-{abs(virtual_id)}"

        amount = float(snap.amount or 0.0)

        items.append(
            {
                "id": virtual_id,
                "client_id": client_id,
                "fund_type": fund_type,
                "company_name": company_name,
                "fund_name": fund_name,
                # Prefer the official market fund code from SavingProduct when available
                "fund_code": (sp.fund_code if sp and sp.fund_code else (fund_code or fund_number or "")),
                "yield_1yr": sp.yield_1yr if sp else None,
                "yield_3yr": sp.yield_3yr if sp else None,
                "personal_number": personal_number,
                "management_fee_balance": amount,
                "management_fee_contributions": None,
                "accumulated_amount": amount,
                "employment_status": None,
                "has_regular_contributions": None,
                "is_virtual": True,
            }
        )
        virtual_id -= 1

    # Local canonicalization by personal number: group multiple tracks of the same
    # personal_number into a single row with aggregated balance and the name of
    # the track that has the highest balance.
    by_personal: Dict[str, List[Dict[str, Any]]] = {}
    standalone_items: List[Dict[str, Any]] = []

    for item in items:
        raw_personal = (item.get("personal_number") or "").strip()
        if not raw_personal:
            standalone_items.append(item)
            continue

        # Canonical personal key:
        # - If the value contains parentheses, group by the value inside the first pair
        #   of parentheses (e.g. "(6077389) 627-274-19096" -> "6077389").
        # - Otherwise, group by the full trimmed string.
        canonical = raw_personal
        start = raw_personal.find("(")
        end = raw_personal.find(")", start + 1) if start != -1 else -1
        if start != -1 and end != -1 and end > start + 1:
            inner = raw_personal[start + 1 : end].strip()
            if inner:
                canonical = inner

        if canonical not in by_personal:
            by_personal[canonical] = []
        by_personal[canonical].append(item)

    grouped: List[Dict[str, Any]] = []

    # First keep items without personal number as-is
    grouped.extend(standalone_items)

    # Then aggregate items that share the same personal number
    for personal, bucket in by_personal.items():
        if len(bucket) == 1:
            grouped.append(bucket[0])
            continue

        total_amount = 0.0
        best_item: Dict[str, Any] | None = None
        best_amount = -1.0

        for it in bucket:
            amount_val = it.get("accumulated_amount")
            try:
                numeric_amount = float(amount_val) if amount_val is not None else 0.0
            except Exception:
                numeric_amount = 0.0

            total_amount += numeric_amount

            if best_item is None or numeric_amount > best_amount:
                best_item = it
                best_amount = numeric_amount

        if best_item is None:
            # Fallback: if something went wrong, just extend all items as-is
            grouped.extend(bucket)
            continue

        # Clone the representative item and overwrite the balance fields with the
        # aggregated balance across all tracks for this personal number.
        rep = dict(best_item)
        rep["accumulated_amount"] = total_amount
        rep["management_fee_balance"] = total_amount

        # If at least one item in the group can be mapped to a SavingProduct by
        # fund_code, prefer the canonical market data for company, fund name,
        # type and code from that SavingProduct.
        canonical_sp: SavingProduct | None = None
        for it in bucket:
            code_val = (str(it.get("fund_code") or "").strip())
            if not code_val:
                continue
            sp_match = saving_by_code.get(code_val)
            if sp_match is not None:
                canonical_sp = sp_match
                break

        if canonical_sp is not None:
            rep["company_name"] = canonical_sp.company_name or ""
            rep["fund_name"] = canonical_sp.fund_name or ""
            rep["fund_type"] = canonical_sp.fund_type or ""
            rep["fund_code"] = canonical_sp.fund_code or ""

        grouped.append(rep)

    return grouped


def list_new_products_for_client(db: Session, client_id: int) -> List[NewProduct]:
    """Return all new products for a specific client."""
    return (
        db.query(NewProduct)
        .filter(NewProduct.client_id == client_id)
        .order_by(NewProduct.created_at.desc())
        .all()
    )


def create_new_product_for_client(
    db: Session,
    client_id: int,
    new_product_in: NewProductCreate,
) -> NewProduct:
    """Create a new product for the given client."""
    existing_product_id: int | None = None

    raw_existing_id = new_product_in.existingProductId
    if raw_existing_id is not None:
        if raw_existing_id > 0:
            # Regular existing product persisted in justification DB
            existing_product_id = raw_existing_id
        else:
            # Negative ids represent virtual existing products derived from CRM snapshots
            # in list_existing_products_view_for_client. For such ids, we materialize a
            # real ExistingProduct row so that the new product can point to a concrete
            # DB record instead of a virtual entry.
            existing_view_items = list_existing_products_view_for_client(db, client_id)
            virtual_item = None
            for item in existing_view_items:
                if item.get("id") == raw_existing_id:
                    virtual_item = item
                    break

            if virtual_item is not None:
                existing_row = ExistingProduct(
                    client_id=client_id,
                    fund_type=virtual_item.get("fund_type") or "",
                    company_name=virtual_item.get("company_name") or "",
                    fund_name=virtual_item.get("fund_name") or "",
                    fund_code=virtual_item.get("fund_code") or "",
                    yield_1yr=virtual_item.get("yield_1yr"),
                    yield_3yr=virtual_item.get("yield_3yr"),
                    personal_number=virtual_item.get("personal_number"),
                    management_fee_balance=virtual_item.get("management_fee_balance"),
                    management_fee_contributions=virtual_item.get(
                        "management_fee_contributions"
                    ),
                    accumulated_amount=virtual_item.get("accumulated_amount"),
                    employment_status=virtual_item.get("employment_status"),
                    has_regular_contributions=virtual_item.get("has_regular_contributions"),
                )
                db.add(existing_row)
                db.commit()
                db.refresh(existing_row)
                existing_product_id = existing_row.id

    new_product = NewProduct(
        client_id=client_id,
        existing_product_id=existing_product_id,
        fund_type=new_product_in.fundType,
        company_name=new_product_in.companyName,
        fund_name=new_product_in.fundName,
        fund_code=new_product_in.fundCode,
        yield_1yr=new_product_in.yield1yr,
        yield_3yr=new_product_in.yield3yr,
        personal_number=new_product_in.personalNumber,
        management_fee_balance=new_product_in.managementFeeBalance,
        management_fee_contributions=new_product_in.managementFeeContributions,
        accumulated_amount=new_product_in.accumulatedAmount,
        employment_status=new_product_in.employmentStatus,
        has_regular_contributions=new_product_in.hasRegularContributions,
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


def list_form_instances_for_new_product(db: Session, new_product_id: int) -> List[FormInstance]:
    """Return all form instances for a specific new product."""
    return (
        db.query(FormInstance)
        .filter(FormInstance.new_product_id == new_product_id)
        .order_by(FormInstance.generated_at.desc())
        .all()
    )


def create_form_instance_for_new_product(
    db: Session,
    new_product_id: int,
    form_in: FormInstanceCreate,
) -> FormInstance:
    """Create a new form instance for the given new product."""
    form = FormInstance(
        new_product_id=new_product_id,
        template_filename=form_in.templateFilename,
        status=form_in.status or "נוצר",
        filled_data=form_in.filledData,
        file_output_path=form_in.fileOutputPath,
    )
    db.add(form)
    db.commit()
    db.refresh(form)
    return form


def delete_new_product(db: Session, new_product_id: int) -> bool:
    """Delete a new product by ID. Returns True if deleted, False if not found."""
    product = (
        db.query(NewProduct)
        .filter(NewProduct.id == new_product_id)
        .first()
    )
    if not product:
        return False

    db.delete(product)
    db.commit()
    return True


def delete_existing_product(db: Session, existing_product_id: int) -> bool:
    """Delete an existing product by ID. Returns True if deleted, False if not found."""

    product = (
        db.query(ExistingProduct)
        .filter(ExistingProduct.id == existing_product_id)
        .first()
    )
    if not product:
        return False

    db.delete(product)
    db.commit()
    return True


def delete_form_instance(db: Session, form_instance_id: int) -> bool:
    """Delete a form instance by ID. Returns True if deleted, False if not found."""
    form = (
        db.query(FormInstance)
        .filter(FormInstance.id == form_instance_id)
        .first()
    )
    if not form:
        return False

    db.delete(form)
    db.commit()
    return True


def clear_justification_data(db: Session) -> dict[str, int]:
    """Clear justification-specific data without deleting clients.

    This removes all form instances, new products, existing products and saving
    products, in that order, to respect foreign key relationships.
    """

    deleted_form_instances = db.query(FormInstance).delete()
    deleted_new_products = db.query(NewProduct).delete()
    deleted_existing_products = db.query(ExistingProduct).delete()
    deleted_saving_products = db.query(SavingProduct).delete()
    db.commit()

    return {
        "deletedSavingProducts": deleted_saving_products,
        "deletedExistingProducts": deleted_existing_products,
        "deletedNewProducts": deleted_new_products,
        "deletedFormInstances": deleted_form_instances,
    }
