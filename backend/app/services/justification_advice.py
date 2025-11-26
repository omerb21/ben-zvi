from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import base64
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.models import Client, ExistingProduct, NewProduct
from app.services import justification_b1 as justification_b1_service
from app.services import justification_forms as justification_forms_service


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
        "fund_name": "אלטשулер שחם פנסיה כללית 1329",
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


def _get_templates_env() -> Environment:
    base_dir = Path(__file__).resolve().parent.parent
    templates_dir = base_dir / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    def _url_for(endpoint: str, filename: str) -> str:
        if endpoint == "static":
            return f"/static/{filename}"
        return filename

    env.globals["url_for"] = _url_for
    return env


def build_advice_html(db: Session, client: Client, include_print_button: bool = True) -> str:
    tables = build_tables(client)
    coverage_tables = build_coverage_tables(db, client, tables)

    client_view: Dict[str, Any] = {
        "first_name": client.first_name or "",
        "last_name": client.last_name or "",
        "national_id": client.id_number or "",
        "date_of_birth": client.birth_date,
        "marital_status": client.marital_status or "",
        "employment_status": None,
        "retirement_income": None,
        "insurance_needs": None,
        "existing_products": list(client.existing_products or []),
        "new_products": list(client.new_products or []),
    }

    env = _get_templates_env()
    template = env.get_template("advice_print.html")
    now = date.today()

    base_dir = Path(__file__).resolve().parent.parent
    logo_path = base_dir / "static" / "logo.png"
    logo_data_url = ""
    try:
        if logo_path.is_file():
            logo_bytes = logo_path.read_bytes()
            logo_b64 = base64.b64encode(logo_bytes).decode("ascii")
            logo_data_url = f"data:image/png;base64,{logo_b64}"
    except Exception:
        logo_data_url = ""

    primary_sign_path = base_dir / "static" / "signature.jpg"
    fallback_sign_path = base_dir / "static" / "sign.jpg"
    signature_data_url = ""
    try:
        sign_path = primary_sign_path if primary_sign_path.is_file() else fallback_sign_path
        if sign_path.is_file():
            sign_bytes = sign_path.read_bytes()
            sign_b64 = base64.b64encode(sign_bytes).decode("ascii")
            signature_data_url = f"data:image/jpeg;base64,{sign_b64}"
    except Exception:
        signature_data_url = ""

    # Client signature (from signing flow), if available as PNG in the
    # client's export directory. This is used to render the client's
    # signature image in the advice document at the designated locations.
    client_signature_data_url = ""
    try:
        export_dir = justification_b1_service._get_client_export_dir(client)
        client_sig_path = export_dir / "client_signature.png"
        if client_sig_path.is_file():
            client_sig_bytes = client_sig_path.read_bytes()
            client_sig_b64 = base64.b64encode(client_sig_bytes).decode("ascii")
            client_signature_data_url = f"data:image/png;base64,{client_sig_b64}"
            try:
                print("[advice] client_signature_data_url built from", client_sig_path)
            except Exception:
                pass
        else:
            try:
                print("[advice] client_signature.png not found at", client_sig_path)
            except Exception:
                pass
    except Exception:
        client_signature_data_url = ""

    html = template.render(
        client=client_view,
        tables=tables,
        coverage_tables=coverage_tables,
        now=now,
        logo_data_url=logo_data_url,
        signature_data_url=signature_data_url,
        client_signature_data_url=client_signature_data_url,
        show_print_button=include_print_button,
    )
    return html


def generate_advice_pdf(html: str) -> Optional[bytes]:
    try:
        import shutil
        import subprocess
        from pathlib import Path
        from uuid import uuid4
    except Exception:
        return None

    options = {
        "page-size": "A4",
        "encoding": "UTF-8",
        "load-error-handling": "ignore",
    }

    # backend_root: .../backend
    backend_root = Path(__file__).resolve().parent.parent.parent
    runtime_dir = backend_root / "advice_runtime"
    try:
        runtime_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        return None

    is_windows = os.name == "nt"
    candidate_paths: list[Path] = []
    if is_windows:
        candidate_paths.extend(
            [
                backend_root / "bin" / "wkhtmltopdf.exe",
                Path(r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"),
                Path(r"C:\\Program Files (x86)\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"),
            ]
        )
    else:
        candidate_paths.append(backend_root / "bin" / "wkhtmltopdf")

    wkhtmltopdf_cmd = shutil.which("wkhtmltopdf")
    if not wkhtmltopdf_cmd:
        for candidate in candidate_paths:
            if candidate.is_file():
                wkhtmltopdf_cmd = str(candidate)
                break

    if not wkhtmltopdf_cmd:
        # Debug log for environments (e.g. Render) where wkhtmltopdf is
        # not available or not found in the expected locations.
        try:
            print("[advice] wkhtmltopdf not found; candidate_paths=", candidate_paths)
        except Exception:
            pass
        return None

    html_name = f"advice_{uuid4().hex}.html"
    pdf_name = html_name.replace(".html", ".pdf")
    input_path = runtime_dir / html_name
    output_path = runtime_dir / pdf_name

    try:
        input_path.write_text(html, encoding="utf-8")

        cmd = [wkhtmltopdf_cmd]
        for key, value in options.items():
            cmd.extend([f"--{key}", str(value)])
        cmd.extend([str(input_path), str(output_path)])

        try:
            print("[advice] running wkhtmltopdf:", cmd, "cwd=", runtime_dir)
        except Exception:
            pass

        result = subprocess.run(
            cmd,
            cwd=str(runtime_dir),
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            try:
                print("[advice] wkhtmltopdf failed, code=", result.returncode)
                if result.stdout:
                    print("[advice] stdout:", result.stdout[:4000])
                if result.stderr:
                    print("[advice] stderr:", result.stderr[:4000])
            except Exception:
                pass
            return None

        if not output_path.is_file():
            try:
                print("[advice] wkhtmltopdf returned 0 but output PDF not found:", output_path)
            except Exception:
                pass
            return None

        pdf_bytes = output_path.read_bytes()
        return pdf_bytes
    except Exception as exc:
        try:
            print("[advice] exception during wkhtmltopdf run:", repr(exc))
        except Exception:
            pass
        return None
    finally:
        try:
            if input_path.is_file():
                input_path.unlink()
        except Exception:
            pass
        try:
            if output_path.is_file():
                output_path.unlink()
        except Exception:
            pass


def save_advice_pdf_for_client(db: Session, client: Client) -> None:
    """(Re)generate the advice PDF for a client and save it to the
    standard export path. If generation fails, this function does
    nothing and does not raise.

    Used after the client has signed, so that the advice PDF can
    include the client's signature image when available.
    """

    display_name = client.full_name or client.id_number or f"client_{client.id}"
    safe_name_chars: List[str] = []
    for ch in display_name:
        if ch.isalnum() or "\u0590" <= ch <= "\u05FF":
            safe_name_chars.append(ch)
        else:
            safe_name_chars.append("_")
    safe_name = "".join(safe_name_chars)

    ascii_safe_name_chars: List[str] = []
    for ch in safe_name:
        if ch.isascii() and (ch.isalnum() or ch in "-_"):
            ascii_safe_name_chars.append(ch)
        else:
            ascii_safe_name_chars.append("_")
    ascii_safe_name = "".join(ascii_safe_name_chars) or f"client_{client.id}"

    filename = f"justification_{ascii_safe_name}.pdf"

    export_dir = justification_b1_service._get_client_export_dir(client)
    save_path = export_dir / filename

    html = build_advice_html(db, client)
    pdf_bytes = generate_advice_pdf(html)
    if pdf_bytes is None:
        try:
            print("[advice] save_advice_pdf_for_client: PDF generation failed for client", client.id)
        except Exception:
            pass
        return

    # Overlay the client's drawn signature image onto the advice PDF, if
    # available. This ensures that the client signature appears in the
    # advice document even if the HTML-to-PDF engine behaves differently
    # across environments.
    try:
        client_sig_path = export_dir / "client_signature.png"
        if client_sig_path.is_file():
            try:
                print("[advice] overlay: found client_signature.png at", client_sig_path)
            except Exception:
                pass
            client_sig_bytes = client_sig_path.read_bytes()
            client_sig_b64 = base64.b64encode(client_sig_bytes).decode("ascii")
            client_sig_data_url = f"data:image/png;base64,{client_sig_b64}"
            pdf_bytes = justification_forms_service.apply_overlay_to_pdf(
                pdf_bytes,
                free_text=None,
                signature_image_data=client_sig_data_url,
                signature_position="bottom_right",
            )
            try:
                print("[advice] overlay: applied client signature overlay for client", client.id)
            except Exception:
                pass
        else:
            try:
                print("[advice] overlay: client_signature.png not found at", client_sig_path)
            except Exception:
                pass
    except Exception:
        # If anything goes wrong with overlaying the signature, we still
        # keep the base advice PDF without failing the whole flow.
        try:
            print("[advice] overlay: exception while applying client signature overlay for client", client.id)
        except Exception:
            pass
        pass

    try:
        save_path.write_bytes(pdf_bytes)
    except Exception:
        pass
