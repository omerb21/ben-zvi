from typing import Dict, List, Any
from xml.etree import ElementTree as ET

from sqlalchemy.orm import Session

from app.models import SavingProduct
from app.schemas.justification import SavingProductCreate
from app.services import imports_saving_products_helpers as _helpers
from app.utils.strings import strip_or_empty as _strip_or_empty


def _to_float_percent(value: str | None) -> float | None:
    return _helpers._to_float_percent(value)


def _fallback_float_percent(primary: str | None, fallback: str | None) -> float | None:
    return _helpers._fallback_float_percent(primary, fallback)


def _update_saving_product_from_schema(sp: SavingProduct, p: SavingProductCreate) -> bool:
    return _helpers._update_saving_product_from_schema(sp, p)


def _create_saving_product(
    *,
    fund_type: str,
    company_name: str,
    fund_name: str,
    fund_code: str,
    yield_1yr: float | None,
    yield_3yr: float | None,
    risk_level: float | None,
    guaranteed_return: str | None,
) -> SavingProduct:
    return _helpers._create_saving_product(
        fund_type=fund_type,
        company_name=company_name,
        fund_name=fund_name,
        fund_code=fund_code,
        yield_1yr=yield_1yr,
        yield_3yr=yield_3yr,
        risk_level=risk_level,
        guaranteed_return=guaranteed_return,
    )


def _saving_product_compound_key(
    fund_type: str | None,
    company_name: str | None,
    fund_name: str | None,
    fund_code: str | None,
) -> tuple[str, str, str, str]:
    return _helpers._saving_product_compound_key(
        fund_type,
        company_name,
        fund_name,
        fund_code,
    )


def import_saving_products_from_gemelnet_xml(db: Session, file_bytes: bytes) -> Dict[str, int]:
    root = ET.fromstring(file_bytes)

    existing = db.query(SavingProduct).all()
    index: dict[tuple[str, str, str, str], SavingProduct] = {}
    for sp in existing:
        key = _saving_product_compound_key(
            sp.fund_type,
            sp.company_name,
            sp.fund_name,
            sp.fund_code,
        )
        index[key] = sp

    created = 0
    updated = 0
    rows_processed = 0
    duplicates_skipped = 0

    for elem in root.findall(".//Row"):
        rows_processed += 1

        fund_code = _strip_or_empty(elem.findtext("ID"))
        fund_name = _strip_or_empty(elem.findtext("SHM_KUPA"))
        company_name = _strip_or_empty(elem.findtext("SHM_HEVRA_MENAHELET"))

        if not fund_code or not fund_name or not company_name:
            continue

        # Yields: mirror the legacy justification logic
        yield_1yr = _fallback_float_percent(
            elem.findtext("TSUA_MITZTABERET_LETKUFA"),
            elem.findtext("TSUA_SHNATIT_MEMUZAAT_3_SHANIM"),
        )
        yield_3yr = _fallback_float_percent(
            elem.findtext("TSUA_MITZTABERET_36_HODASHIM"),
            elem.findtext("TSUA_MEMUZAAT_36_HODASHIM"),
        )

        # Fund type heuristics: default "גמל" with special handling for
        # "גמל להשקעה" ו"השתלמות" כמו במערכת ההנמקה הישנה.
        fund_type = "גמל"
        text_for_type = f"{fund_name} {company_name}"
        if "גמל להשקעה" in text_for_type:
            fund_type = "גמל להשקעה"
        elif (("חסכון פלוס" in (fund_name or "")) or ("חיסכון פלוס" in (fund_name or ""))) and (
            "אלטשולר" in (company_name or "")
        ):
            fund_type = "גמל להשקעה"
        elif "השתלמות" in text_for_type:
            fund_type = "השתלמות"

        risk_level = None
        guaranteed_return = None

        key = _saving_product_compound_key(
            fund_type,
            company_name,
            fund_name,
            fund_code,
        )
        sp = index.get(key)
        if sp is None:
            sp = _create_saving_product(
                fund_type=fund_type,
                company_name=company_name,
                fund_name=fund_name,
                fund_code=fund_code,
                yield_1yr=yield_1yr,
                yield_3yr=yield_3yr,
                risk_level=risk_level,
                guaranteed_return=guaranteed_return,
            )
            db.add(sp)
            index[key] = sp
            created += 1
        else:
            prev = (
                sp.yield_1yr,
                sp.yield_3yr,
                sp.risk_level,
                sp.guaranteed_return,
            )
            sp.yield_1yr = yield_1yr
            sp.yield_3yr = yield_3yr
            sp.risk_level = risk_level
            sp.guaranteed_return = guaranteed_return
            now = (
                sp.yield_1yr,
                sp.yield_3yr,
                sp.risk_level,
                sp.guaranteed_return,
            )
            if now != prev:
                updated += 1
            else:
                duplicates_skipped += 1

    db.commit()

    return {
        "createdSavingProducts": created,
        "updatedSavingProducts": updated,
        "rowsProcessed": rows_processed,
        "duplicatesSkipped": duplicates_skipped,
    }


def sync_saving_products_batch(db: Session, products: List[SavingProductCreate]) -> Dict[str, int]:
    existing = db.query(SavingProduct).all()
    # Index by fund_code which should be unique enough for updates
    index: dict[str, SavingProduct] = {}
    for sp in existing:
        if sp.fund_code:
            index[sp.fund_code] = sp
    
    created = 0
    updated = 0
    
    for p in products:
        sp = index.get(p.fundCode)
        if sp:
            # Update
            changed = _update_saving_product_from_schema(sp, p)
            
            if changed:
                updated += 1
        else:
            # Create
            sp = _create_saving_product(
                fund_type=p.fundType,
                company_name=p.companyName,
                fund_name=p.fundName,
                fund_code=p.fundCode,
                yield_1yr=p.yield1yr,
                yield_3yr=p.yield3yr,
                risk_level=p.riskLevel,
                guaranteed_return=p.guaranteedReturn,
            )
            db.add(sp)
            index[p.fundCode] = sp
            created += 1
            
    db.commit()
    return {"created": created, "updated": updated}
