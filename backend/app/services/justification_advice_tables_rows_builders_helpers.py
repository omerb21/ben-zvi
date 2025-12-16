from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.models import Client, ExistingProduct, NewProduct
from app.services import justification_advice_tables_rows_utils as _utils


_RECOMMENDATION_TEXT = (
    "שיקולים לבחירת הקופה: 1. רמת שירות גבוהה של הגוף המוסדי. 2. רמת תפעול גבוהה של הגוף המוסדי. 3. רמת ניהול השקעות גבוהה של הגוף המוסדי."
)


def _build_recommendation_row() -> Dict[str, Any]:
    return {
        "recommendation": _RECOMMENDATION_TEXT,
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


def _append_fund_code_to_track_name(row: Dict[str, Any], fund_code: str | None) -> Dict[str, Any]:
    if fund_code:
        row["track_name"] = f"{row['track_name']} ({fund_code})"
    return row


def build_existing_row(client: Client, ex: ExistingProduct) -> Dict[str, Any]:
    yrs = _utils.years_to_67(client.birth_date)
    accumulated = ex.accumulated_amount or 0.0
    raw_fee_pct = ex.management_fee_balance
    if (
        raw_fee_pct is not None
        and accumulated
        and raw_fee_pct > 100
        and abs(raw_fee_pct - accumulated) < 1.0
    ):
        safe_fee_pct = None
    else:
        safe_fee_pct = raw_fee_pct

    fv67 = _utils.fv(balance=accumulated, years=yrs)
    fee = _utils.fee_cost(
        balance=accumulated,
        fee_pct=(safe_fee_pct / 100.0) if safe_fee_pct else 0,
        years=yrs,
    )

    fund_name = _utils._append_personal_number_to_fund_name(
        ex.fund_type,
        ex.fund_name,
        getattr(ex, "personal_number", None),
    )

    norm_type = _utils.normalize_fund_type(ex.fund_type)

    return {
        "id": ex.id,
        "recommendation": "לבטל"
        if norm_type in ["גמל", "גמל להשקעה", "השתלמות"] and _utils.has_replacement(ex)
        else "להשאיר",
        "product_type": f"קופת {norm_type}",
        "company_name": ex.company_name,
        "fund_name": fund_name,
        "track_name": fund_name,
        "guaranteed_return": "לא",
        "yield_1yr": _utils._format_yield(ex.yield_1yr),
        "yield_3yr": _utils._format_yield(ex.yield_3yr),
        "mgmt_fee_dep": ex.management_fee_contributions or "",
        "mgmt_fee_bal": safe_fee_pct or "",
        "balance": _utils._format_balance(accumulated),
        "forecast": f"גיל פרישה 67 הון צפוי ללא הפקדות {fv67:,.0f}₪ דמי ניהול של {fee:,.0f}₪",
        "cost": "",
    }


def build_new_row(
    client: Client,
    new: NewProduct,
    accumulated_override: Optional[float] = None,
) -> Dict[str, Any]:
    yrs = _utils.years_to_67(client.birth_date)
    base_accumulated = new.accumulated_amount or 0
    accumulated = accumulated_override if accumulated_override is not None else base_accumulated
    fv67 = _utils.fv(balance=accumulated, years=yrs)
    fee = _utils.fee_cost(
        balance=accumulated,
        fee_pct=new.management_fee_balance / 100 if new.management_fee_balance else 0,
        years=yrs,
    )

    fund_name = _utils._append_personal_number_to_fund_name(
        new.fund_type,
        new.fund_name,
        getattr(new, "personal_number", None),
    )

    norm_type = _utils.normalize_fund_type(new.fund_type)

    return {
        "id": new.id,
        "recommendation": "להצטרף",
        "product_type": f"קופת {norm_type}",
        "company_name": new.company_name,
        "fund_name": fund_name,
        "track_name": fund_name,
        "guaranteed_return": "לא",
        "yield_1yr": _utils._format_yield(new.yield_1yr),
        "yield_3yr": _utils._format_yield(new.yield_3yr),
        "mgmt_fee_dep": new.management_fee_contributions or "",
        "mgmt_fee_bal": new.management_fee_balance or "",
        "balance": _utils._format_balance(accumulated),
        "forecast": f"גיל פרישה 67 הון צפוי ללא הפקדות {fv67:,.0f} דמי ניהול של {fee:,.0f}",
        "cost": "",
    }


def _build_existing_row_with_fund_code(client: Client, existing: ExistingProduct) -> Dict[str, Any]:
    row = build_existing_row(client, existing)
    return _append_fund_code_to_track_name(row, existing.fund_code)


def _build_new_row_with_fund_code(
    client: Client,
    new: NewProduct,
    accumulated_override: Optional[float] = None,
) -> Dict[str, Any]:
    row = build_new_row(client, new, accumulated_override)
    return _append_fund_code_to_track_name(row, new.fund_code)


def _build_new_rows_with_fund_code(
    client: Client,
    new_list: List[NewProduct],
    accumulated_override: Optional[float],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for new in new_list:
        rows.append(_build_new_row_with_fund_code(client, new, accumulated_override))
    return rows


STATIC_ROWS_COMPARISON: List[Dict[str, Any]] = [
    {
        "recommendation": "חלופה 1",
        "product_type": "קרן פנסיה",
        "company_name": "אלטשולר שחם גמל ופנסיה בע\"מ",
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
        "company_name": "אלטשולר שחם גמל ופנסיה בע\"מ",
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
    yrs = _utils.years_to_67(client.birth_date)
    result: List[Dict[str, Any]] = []

    for i, row in enumerate(STATIC_ROWS_COMPARISON):
        new_row = row.copy()
        acc_value = getattr(existing, "accumulated_amount", None) or 0.0
        new_row["balance"] = _utils._format_balance(acc_value)
        fv67 = _utils.fv(balance=acc_value, years=yrs)

        fee = _utils.fee_cost(balance=acc_value, fee_pct=_utils._static_fee_pct_for_index(i), years=yrs)

        new_row[
            "forecast"
        ] = f"גיל פרישה 67 הון צפוי ללא הפקדות {fv67:,.0f} דמי ניהול של {fee:,.0f}"
        new_row["cost"] = ""
        result.append(new_row)

    return result
