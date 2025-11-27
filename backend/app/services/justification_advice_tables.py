from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import Client, ExistingProduct, NewProduct


INTEREST_RATE = 0.03


def years_to_67(birth: date) -> int:
    return max(0, 67 - (date.today().year - birth.year))


def fv(balance: float | None, years: int, r: float = INTEREST_RATE) -> float:
    if balance is None or years <= 0:
        return 0.0
    return round(float(balance) * (1 + r) ** years, 2)


def fee_cost(balance: float | None, fee_pct: float | None, years: int) -> float:
    if balance is None or not fee_pct or years <= 0:
        return 0.0
    return round(float(balance) * float(fee_pct) * years, 2)


def has_replacement(existing_product: ExistingProduct) -> bool:
    return any(
        new.fund_type == existing_product.fund_type for new in existing_product.new_products
    )


def build_existing_row(client: Client, ex: ExistingProduct) -> Dict[str, Any]:
    yrs = years_to_67(client.birth_date)
    accumulated = ex.accumulated_amount or 0.0
    fv67 = fv(balance=accumulated, years=yrs)
    fee = fee_cost(
        balance=accumulated,
        fee_pct=ex.management_fee_balance / 100 if ex.management_fee_balance else 0,
        years=yrs,
    )

    fund_name = ex.fund_name
    if (
        ex.fund_type in ["גמל", "גמל להשקעה", "השתלמות"]
        and hasattr(ex, "personal_number")
        and ex.personal_number
    ):
        fund_name = f"{fund_name} (מס' קופה: {ex.personal_number})"

    return {
        "id": ex.id,
        "recommendation": "לבטל"
        if ex.fund_type in ["גמל", "גמל להשקעה", "השתלמות"] and has_replacement(ex)
        else "להשאיר",
        "product_type": f"קופת {ex.fund_type}",
        "company_name": ex.company_name,
        "fund_name": fund_name,
        "track_name": fund_name,
        "guaranteed_return": "לא",
        "yield_1yr": f"{ex.yield_1yr or ''}%" if ex.yield_1yr is not None else "אין נתון",
        "yield_3yr": f"{ex.yield_3yr or ''}%" if ex.yield_3yr is not None else "אין נתון",
        "mgmt_fee_dep": ex.management_fee_contributions or "",
        "mgmt_fee_bal": ex.management_fee_balance or "",
        "balance": f"{accumulated:,.0f}" if accumulated else "לא רלוונטי",
        "forecast": f"גיל פרישה 67 הון צפוי ללא הפקדות {fv67:,.0f}₪ דמי ניהול של {fee:,.0f}₪",
        "cost": "",
    }


def build_new_row(
    client: Client,
    new: NewProduct,
    accumulated_override: Optional[float] = None,
) -> Dict[str, Any]:
    yrs = years_to_67(client.birth_date)
    base_accumulated = new.accumulated_amount or 0
    accumulated = accumulated_override if accumulated_override is not None else base_accumulated
    fv67 = fv(balance=accumulated, years=yrs)
    fee = fee_cost(
        balance=accumulated,
        fee_pct=new.management_fee_balance / 100 if new.management_fee_balance else 0,
        years=yrs,
    )

    fund_name = new.fund_name
    if (
        new.fund_type in ["גמל", "גמל להשקעה", "השתלמות"]
        and hasattr(new, "personal_number")
        and new.personal_number
    ):
        fund_name = f"{fund_name} (מס' קופה: {new.personal_number})"

    return {
        "id": new.id,
        "recommendation": "להצטרף",
        "product_type": f"קופת {new.fund_type}",
        "company_name": new.company_name,
        "fund_name": fund_name,
        "track_name": fund_name,
        "guaranteed_return": "לא",
        "yield_1yr": f"{new.yield_1yr or ''}%" if new.yield_1yr is not None else "אין נתון",
        "yield_3yr": f"{new.yield_3yr or ''}%" if new.yield_3yr is not None else "אין נתון",
        "mgmt_fee_dep": new.management_fee_contributions or "",
        "mgmt_fee_bal": new.management_fee_balance or "",
        "balance": f"{accumulated:,.0f}" if accumulated else "לא רלוונטי",
        "forecast": f"גיל פרישה 67 הון צפוי ללא הפקדות {fv67:,.0f} דמי ניהול של {fee:,.0f}",
        "cost": "",
    }


STATIC_ROWS_COMPARISON: List[Dict[str, Any]] = [
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
        "balance": "",
        "forecast": "",
        "cost": "",
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
        "balance": "",
        "forecast": "",
        "cost": "",
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
        "balance": "",
        "forecast": "",
        "cost": "",
    },
]


def build_static_rows(client: Client, existing: ExistingProduct) -> List[Dict[str, Any]]:
    yrs = years_to_67(client.birth_date)
    result: List[Dict[str, Any]] = []

    for i, row in enumerate(STATIC_ROWS_COMPARISON):
        new_row = row.copy()
        acc_value = getattr(existing, "accumulated_amount", None) or 0.0
        new_row["balance"] = f"{acc_value:,.0f}" if acc_value else "לא רלוונטי"
        fv67 = fv(balance=acc_value, years=yrs)

        if i == 2:
            fee = fee_cost(balance=acc_value, fee_pct=0.0044, years=yrs)
        else:
            fee = fee_cost(balance=acc_value, fee_pct=0.0022, years=yrs)

        new_row[
            "forecast"
        ] = f"גיל פרישה 67 הון צפוי ללא הפקדות {fv67:,.0f} דמי ניהול של {fee:,.0f}"
        new_row["cost"] = ""
        result.append(new_row)

    return result


def filter_pairs(client: Client) -> List[Tuple[ExistingProduct, List[NewProduct]]]:
    result: List[Tuple[ExistingProduct, List[NewProduct]]] = []

    for existing in client.existing_products:
        new_products = [
            np
            for np in client.new_products
            if np.existing_product_id == existing.id and np.fund_type == existing.fund_type
        ]
        result.append((existing, new_products))

    return result


def build_tables(client: Client) -> List[List[Dict[str, Any]]]:
    tables: List[List[Dict[str, Any]]] = []
    pairs = filter_pairs(client)

    standalone_new_products = [
        np for np in client.new_products if np.existing_product_id is None
    ]

    for standalone_new in standalone_new_products:
        standalone_row = build_new_row(client, standalone_new)
        standalone_row["track_name"] = (
            f"{standalone_row['track_name']} ({standalone_new.fund_code})"
        )

        alternatives_rows: List[Dict[str, Any]] = []
        if standalone_new.fund_type == "גמל":
            temp_existing = type(
                "obj",
                (object,),
                {
                    "accumulated_amount": standalone_new.accumulated_amount or 0,
                    "fund_code": standalone_new.fund_code,
                },
            )
            alternatives_rows = build_static_rows(client, temp_existing)  # type: ignore[arg-type]

        recommendation_row = {
            "recommendation": "שיקולים לבחירת הקופה: 1. רמת שירות גבוהה של הגוף המוסדי. 2. רמת תפעול גבוהה של הגוף המוסדי. 3. רמת ניהול השקעות גבוהה של הגוף המוסדי.",
            "product_type": "",
            "company_name": "",
            "fund_name": "",
            "track_name": "",
            "guaranteed_return": "",
            "yield_1yr": "",
            "mgmt_fee_dep": "",
            "mgmt_fee_bal": "",
            "balance": "",
            "forecast": "",
            "cost": "",
        }

        table = [standalone_row] + alternatives_rows + [recommendation_row]
        tables.append(table)

    for ex, new_list in pairs:
        share_amount: Optional[float] = None
        if ex.accumulated_amount is not None and len(new_list) > 1:
            total = ex.accumulated_amount or 0.0
            count = float(len(new_list))
            share_amount = total / count if count > 0 else 0.0

        if ex.fund_type == "גמל":
            if new_list:
                existing_row = build_existing_row(client, ex)
                existing_row["track_name"] = (
                    f"{existing_row['track_name']} ({ex.fund_code})"
                )

                new_rows: List[Dict[str, Any]] = []
                for new in new_list:
                    new_row = build_new_row(client, new, share_amount)
                    new_row["track_name"] = (
                        f"{new_row['track_name']} ({new.fund_code})"
                    )
                    new_rows.append(new_row)

                alternatives_rows = build_static_rows(client, ex)

                recommendation_row = {
                    "recommendation": "שיקולים לבחירת הקופה: 1. רמת שירות גבוהה של הגוף המוסדי. 2. רמת תפעול גבוהה של הגוף המוסדי. 3. רמת ניהול השקעות גבוהה של הגוף המוסדי.",
                    "product_type": "",
                    "company_name": "",
                    "fund_name": "",
                    "track_name": "",
                    "guaranteed_return": "",
                    "yield_1yr": "",
                    "mgmt_fee_dep": "",
                    "mgmt_fee_bal": "",
                    "balance": "",
                    "forecast": "",
                    "cost": "",
                }

                table = [existing_row] + new_rows + alternatives_rows + [recommendation_row]
            else:
                existing_row = build_existing_row(client, ex)
                existing_row["track_name"] = (
                    f"{existing_row['track_name']} ({ex.fund_code})"
                )
                table = [existing_row]
        else:
            if new_list:
                existing_row = build_existing_row(client, ex)
                existing_row["track_name"] = (
                    f"{existing_row['track_name']} ({ex.fund_code})"
                )

                new_rows = []
                for new in new_list:
                    new_row = build_new_row(client, new, share_amount)
                    new_row["track_name"] = (
                        f"{new_row['track_name']} ({new.fund_code})"
                    )
                    new_rows.append(new_row)

                recommendation_row = {
                    "recommendation": "שיקולים לבחירת הקופה: 1. רמת שירות גבוהה של הגוף המוסדי. 2. רמת תפעול גבוהה של הגוף המוסדי. 3. רמת ניהול השקעות גבוהה של הגוף המוסדי.",
                    "product_type": "",
                    "company_name": "",
                    "fund_name": "",
                    "track_name": "",
                    "guaranteed_return": "",
                    "yield_1yr": "",
                    "mgmt_fee_dep": "",
                    "mgmt_fee_bal": "",
                    "balance": "",
                    "forecast": "",
                    "cost": "",
                }

                table = [existing_row] + new_rows + [recommendation_row]
            else:
                existing_row = build_existing_row(client, ex)
                existing_row["track_name"] = (
                    f"{existing_row['track_name']} ({ex.fund_code})"
                )
                table = [existing_row]

        tables.append(table)

    return tables


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


def build_coverage_table_rows(
    existing: Optional[ExistingProduct],
    new: Optional[NewProduct] = None,
    add_alternatives: bool = False,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    def make_row(item: Any, recommendation: str) -> Dict[str, Any]:
        if isinstance(item, (ExistingProduct, NewProduct)):
            return {
                "recommendation": recommendation,
                "product_name": (
                    f"{item.fund_name} (מס' קופה: {item.personal_number})"
                    if hasattr(item, "personal_number") and item.personal_number
                    else item.fund_name
                ),
                "company_name": item.company_name,
                "coverage_type": "אין כיסויים במוצר זה",
                "coverage_amount": "אין כיסויים במוצר זה",
                "monthly_cost": "אין כיסויים במוצר זה",
                "included_in_pension": "",
            }
        return {
            "recommendation": item["recommendation"],
            "product_name": item["fund_name"],
            "company_name": item["company_name"],
            "coverage_type": "אין כיסויים במוצר זה",
            "coverage_amount": "אין כיסויים במוצר זה",
            "monthly_cost": "אין כיסויים במוצר זה",
            "included_in_pension": "",
        }

    if existing is None and new is not None:
        rows.append(make_row(new, "להצטרף"))
        if new.fund_type == "גמל" and add_alternatives:
            for alt_row in STATIC_ROWS_COVERAGE:
                rows.append(make_row(alt_row, alt_row["recommendation"]))
    elif existing is not None:
        rows.append(make_row(existing, "להשאיר" if not new else "להצטרף"))
        if new:
            rows.append(make_row(new, "להצטרף"))
        if existing.fund_type == "גמל" and add_alternatives:
            for alt_row in STATIC_ROWS_COVERAGE:
                rows.append(make_row(alt_row, alt_row["recommendation"]))

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
                existing_product.fund_type == "גמל" and not alternatives_added
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
                    product.fund_type == "גמל" and not alternatives_added
                ),
            )
            if product.fund_type == "גמל":
                alternatives_added = True
            coverage_tables.append(coverage_rows)

    return coverage_tables
