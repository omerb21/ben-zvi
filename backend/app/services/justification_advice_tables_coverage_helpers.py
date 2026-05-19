from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import Client, ExistingProduct, NewProduct
from app.services.justification_advice_tables_rows import _is_normalized_gemel, has_replacement


def _no_coverage_fields() -> Dict[str, Any]:
    return {
        "coverage_type": "אין כיסויים במוצר זה",
        "coverage_amount": "אין כיסויים במוצר זה",
        "monthly_cost": "אין כיסויים במוצר זה",
        "included_in_pension": "",
    }


def _coverage_product_name(fund_name: str | None, personal_number: str | None) -> str | None:
    if personal_number:
        return f"{fund_name} (מס' קופה: {personal_number})"
    return fund_name


def _build_coverage_table_row(item: Any, recommendation: str) -> Dict[str, Any]:
    if isinstance(item, (ExistingProduct, NewProduct)):
        return {
            "recommendation": recommendation,
            "product_name": _coverage_product_name(item.fund_name, item.personal_number),
            "company_name": item.company_name,
            **_no_coverage_fields(),
        }
    return {
        "recommendation": item["recommendation"],
        "product_name": item["fund_name"],
        "company_name": item["company_name"],
        **_no_coverage_fields(),
    }


STATIC_ROWS_COVERAGE: List[Dict[str, Any]] = [
    {
        "recommendation": "חלופה 1",
        "product_type": "קרן פנסיה",
        "company_name": "אלטשולר שחם גמל ופנסיה בע" "מ",
        "fund_name": "אלטשולר שחם פנסיה מקיפה 1328",
        "track_name": "מודל השקעה תלוי גיל, אלטשולר שחם, פנסיה מקיפה, מסלול לבני 50 עד 60, מ.ה 9758",
        "guaranteed_return": "כן, קיימת הבטחת תשואה שנתית של 5.15% (צמודה למדד) על 30% מהנכסים",
        "yield_1yr": "אלטשולר שחם פנסיה מקיפה מסלול לבני 50-60 תאריך תחילת פעילות 12/11/2015",
        "yield_3yr": "אין נתון",
        "mgmt_fee_dep": "1% הטבה למשך תקופה של 10 שנים לאחר מכן ד.נ. מצבירה 6%",
        "mgmt_fee_bal": "0.22% הטבה למשך תקופה של 10 שנים לאחר מכן ד.נ. מצבירה 0.5%",
    },
    {
        "recommendation": "חלופה 2",
        "product_type": "קרן פנסיה",
        "company_name": "אלטשולר שחם גמל ופנסיה בע" "מ",
        "fund_name": "אלטשולר שחם פנסיה כללית 1329",
        "track_name": "מודל השקעה תלוי גיל, אלטשולר שחם, פנסיה מקיפה, מסלול לבני 50 עד 60, מ.ה 9762",
        "guaranteed_return": "לא",
        "yield_1yr": "אלטשולר שחם פנסיה כללית מסלול לבני 50-60 תאריך תחילת פעילות 12/11/2015",
        "yield_3yr": "אין נתון",
        "mgmt_fee_dep": "1% הטבה למשך תקופה של 10 שנים לאחר מכן ד.נ. מצבירה 4%",
        "mgmt_fee_bal": "0.22% הטבה למשך תקופה של 10 שנים לאחר מכן ד.נ. מצבירה 1.05%",
    },
    {
        "recommendation": "חלופה 3",
        "product_type": "פוליסה",
        "company_name": "מגדל",
        "fund_name": "מגדל מסלול לבני 50-60 מ.ה-9604 פוליסה",
        "track_name": "מודל השקעה תלוי גיל, מגדל מסלול לבני 50 עד 60, מ.ה 9604",
        "guaranteed_return": "לא",
        "yield_1yr": "מגדל מסלול לבני 50-60 תאריך תחילת פעילות : פוליסות שהונפקו משנת 2004 ואילך",
        "yield_3yr": "אין נתון",
        "mgmt_fee_dep": "0% קבוע לכל חיי המוצר",
        "mgmt_fee_bal": "דמי ניהול יורדים לפי צבירה",
    },
]


def _append_static_coverage_alternatives(rows: List[Dict[str, Any]]) -> None:
    for alt_row in STATIC_ROWS_COVERAGE:
        rows.append(_build_coverage_table_row(alt_row, alt_row["recommendation"]))


def build_coverage_table_rows(
    existing: Optional[ExistingProduct],
    new: Optional[NewProduct] = None,
    add_alternatives: bool = False,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    if existing is None and new is not None:
        rows.append(_build_coverage_table_row(new, "להצטרף"))
        if new.fund_type == "גמל" and add_alternatives:
            _append_static_coverage_alternatives(rows)
    elif existing is not None:
        existing_recommendation = "לבטל" if has_replacement(existing) else "להשאיר"
        rows.append(_build_coverage_table_row(existing, existing_recommendation))
        if new:
            rows.append(_build_coverage_table_row(new, "להצטרף"))
        if _is_normalized_gemel(existing.fund_type) and add_alternatives:
            _append_static_coverage_alternatives(rows)

    return rows


def build_coverage_tables(
    db: Session,
    client: Client,
    tables: List[List[Dict[str, Any]]],
) -> List[List[Dict[str, Any]]]:
    coverage_tables: List[List[Dict[str, Any]]] = []
    processed_products: set[int] = set()
    alternatives_added = False

    for table in tables:
        if not table:
            continue

        existing_data = table[0] if table else None
        existing_product: Optional[ExistingProduct] = None
        if existing_data and "id" in existing_data:
            existing_id = existing_data.get("id")
            if existing_id is not None:
                existing_product = db.get(ExistingProduct, existing_id)
        if existing_product and existing_product.id not in processed_products:
            processed_products.add(existing_product.id)

            new_products: List[NewProduct] = []
            for row in table[1:]:
                if row.get("recommendation") == "להצטרף" and "id" in row:
                    new_id = row.get("id")
                    if new_id is not None:
                        new_product = db.get(NewProduct, new_id)
                        if new_product:
                            new_products.append(new_product)

            add_alternatives = (
                _is_normalized_gemel(existing_product.fund_type)
                and not alternatives_added
            )
            if add_alternatives:
                alternatives_added = True

            coverage_rows = build_coverage_table_rows(
                existing_product,
                new_products[0] if new_products else None,
                add_alternatives=add_alternatives,
            )
            coverage_tables.append(coverage_rows)

    standalone_products = (
        db.query(NewProduct)
        .filter(NewProduct.client_id == client.id, NewProduct.existing_product_id.is_(None))
        .all()
    )

    for product in standalone_products:
        if product.id not in processed_products:
            processed_products.add(product.id)
            coverage_rows = build_coverage_table_rows(
                None,
                product,
                add_alternatives=(
                    _is_normalized_gemel(product.fund_type)
                    and not alternatives_added
                ),
            )
            if _is_normalized_gemel(product.fund_type):
                alternatives_added = True
            coverage_tables.append(coverage_rows)

    return coverage_tables
