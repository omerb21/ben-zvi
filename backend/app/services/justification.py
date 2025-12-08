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

    Combines real ExistingProduct rows (manually entered / migrated).
    Previously derived virtual products from CRM snapshots, but this logic is now
    moved to on-demand sync (sync_client_products_from_crm).
    """

    # Real existing products from justification DB
    real_products = list_existing_products_for_client(db, client_id)

    items: List[Dict[str, Any]] = []

    for p in real_products:
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

    return items


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


def sync_client_products_from_crm(db: Session, client_id: int) -> int:
    """Sync CRM snapshots to existing products for a client.

    This takes the latest snapshots, groups them by personal number (canonicalization),
    matches them with market products, and then upserts them into the ExistingProduct table.
    """
    # 1. Fetch active snapshots for client
    snapshots = (
        db.query(Snapshot)
        .filter(Snapshot.client_id == client_id, Snapshot.is_active.is_(True))
        .all()
    )
    if not snapshots:
        return 0

    # 2. Keep latest snapshot per (fund_code, fund_number)
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
        return 0

    # 3. Load saving products for matching
    saving_products = db.query(SavingProduct).all()
    saving_by_code: Dict[str, SavingProduct] = {}
    for sp in saving_products:
        code = (sp.fund_code or "").strip()
        if code and code not in saving_by_code:
            saving_by_code[code] = sp

    # 4. Create intermediate items
    items: List[Dict[str, Any]] = []
    
    for (fund_code, fund_number), snap in latest_by_key.items():
        # Match logic (copied from list_existing_products_view_for_client)
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

        if sp is None:
            clean_code = (fund_code or "").strip()
            if clean_code:
                sp = saving_by_code.get(clean_code)

        fund_type = (snap.fund_type or (sp.fund_type if sp else "")) or ""
        fund_name = (snap.fund_name or (sp.fund_name if sp else "")) or ""
        company_name = (sp.company_name if sp else get_source_display_name(snap.source or "")) or ""

        if not fund_name and not company_name and not fund_type:
            continue

        # Use fund_code as personal_number basis if fund_number is missing, but prefer original raw value
        personal_number = fund_number or fund_code
        
        # Fallback for missing or placeholder personal numbers to avoid uniqueness constraint violations
        if not personal_number or personal_number.strip() in ["לא זמין", "לא ידוע", "-"]:
             # Create a deterministic synthetic ID based on the snapshot key properties
             import hashlib
             key_str = f"{fund_code}|{fund_number}|{fund_name}|{fund_type}"
             hash_part = hashlib.md5(key_str.encode("utf-8")).hexdigest()[:8]
             personal_number = f"CRM-{client_id}-{hash_part}"

        amount = float(snap.amount or 0.0)

        items.append({
            "fund_type": fund_type,
            "company_name": company_name,
            "fund_name": fund_name,
            "fund_code": (sp.fund_code if sp and sp.fund_code else (fund_code or fund_number or "")),
            "yield_1yr": sp.yield_1yr if sp else None,
            "yield_3yr": sp.yield_3yr if sp else None,
            "personal_number": personal_number,
            "accumulated_amount": amount,
            "management_fee_balance": None,
            "management_fee_contributions": None,
            "employment_status": None,
            "has_regular_contributions": None,
            "raw_fund_code": fund_code, # Keep for matching
        })

    # 5. Group by canonical personal number
    by_personal: Dict[str, List[Dict[str, Any]]] = {}
    for item in items:
        raw_personal = (item.get("personal_number") or "").strip()
        if not raw_personal:
            continue

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

    count_updated = 0

    # 6. Upsert into DB
    for personal_key, bucket in by_personal.items():
        if not bucket:
            continue
            
        # Aggregate amounts
        total_amount = sum(float(it.get("accumulated_amount") or 0.0) for it in bucket)
        
        # Pick best item for metadata (one with highest amount)
        best_item = max(bucket, key=lambda x: float(x.get("accumulated_amount") or 0.0))
        
        # Determine the final personal number to store.
        # We need to be consistent. If we already have a product with this canonical key, use its personal_number.
        # Otherwise, use the best_item's personal_number.
        
        # Check if product exists (by canonical match)
        # Since we can't easily query canonical in SQL, we fetch all for client and filter in python,
        # or we just try to find exact match on personal_number from the bucket.
        # But wait, existing products might have different formatting.
        
        # Strategy: 
        # 1. Fetch all existing products for client.
        # 2. Calculate canonical key for each.
        # 3. Find match.
        
        existing_products = list_existing_products_for_client(db, client_id)
        target_product = None
        
        for ep in existing_products:
            ep_personal = (ep.personal_number or "").strip()
            ep_canonical = ep_personal
            start = ep_personal.find("(")
            end = ep_personal.find(")", start + 1) if start != -1 else -1
            if start != -1 and end != -1 and end > start + 1:
                inner = ep_personal[start + 1 : end].strip()
                if inner:
                    ep_canonical = inner
            
            if ep_canonical == personal_key:
                target_product = ep
                break
        
        if target_product:
            # Update
            target_product.accumulated_amount = total_amount
            # target_product.management_fee_balance = total_amount

            # Self-healing: fix data corruption from previous sync bug where fee was set to amount.
            # If fee is suspiciously large (> 100) or equals the amount, reset it to None.
            current_fee = target_product.management_fee_balance or 0.0
            if current_fee > 100 and (current_fee == total_amount or current_fee == target_product.accumulated_amount):
                target_product.management_fee_balance = None
            
            # Only update other fields if they are seemingly valid in the new data
            if best_item["company_name"]: target_product.company_name = best_item["company_name"]
            if best_item["fund_name"]: target_product.fund_name = best_item["fund_name"]
            if best_item["fund_type"]: target_product.fund_type = best_item["fund_type"]
            if best_item["fund_code"]: target_product.fund_code = best_item["fund_code"]
            if best_item["yield_1yr"]: target_product.yield_1yr = best_item["yield_1yr"]
            if best_item["yield_3yr"]: target_product.yield_3yr = best_item["yield_3yr"]
            
        else:
            # Create
            target_product = ExistingProduct(
                client_id=client_id,
                fund_type=best_item["fund_type"],
                company_name=best_item["company_name"],
                fund_name=best_item["fund_name"],
                fund_code=best_item["fund_code"],
                yield_1yr=best_item["yield_1yr"],
                yield_3yr=best_item["yield_3yr"],
                personal_number=best_item["personal_number"], # Use the raw one from the best item
                management_fee_balance=None,
                management_fee_contributions=best_item["management_fee_contributions"],
                accumulated_amount=total_amount,
                employment_status=best_item["employment_status"],
                has_regular_contributions=best_item["has_regular_contributions"],
            )
            db.add(target_product)
        
        count_updated += 1
    
    db.commit()
    return count_updated
