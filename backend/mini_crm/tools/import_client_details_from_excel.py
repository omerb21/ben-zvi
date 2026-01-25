"""Import client personal details from an Excel file into the CRM DB.

- Reads uploads/clients.xlsx (or .xls) with pandas.
- Matches existing clients by id_canon (Teudat Zehut).
- Updates missing fields in client and client_details tables
  (first_name, last_name, phone, email, employer, date_of_birth).
- Does NOT create new clients and does NOT overwrite existing
  non-empty values.

Run once from project root:

    python tools/import_client_details_from_excel.py

The Excel file is expected to have at least an `id_canon` column.
Optional columns that will be used if present:
  - first_name
  - last_name
  - phone
  - email
  - employer
  - date_of_birth (YYYY-MM-DD or any parseable date)
"""

from pathlib import Path
import sqlite3
from datetime import datetime
import sys

import pandas as pd

# Ensure project root is on sys.path so we can import app.py when running
# this file as: python tools/import_client_details_from_excel.py
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Reuse DB config and helper from app
from app import DB, upsert_client_details


def _normalize_id(id_value: str) -> str:
    """Normalize ID string similarly to other loaders: strip spaces.

    We do NOT remove leading zeros to avoid changing canonical IDs
    already stored in the DB. The assumption is that Excel uses
    the same representation as `client.id_canon`.
    """
    if id_value is None:
        return ""
    return str(id_value).strip()


def _cell_to_str(value: object) -> str:
    """Convert Excel cell value (possibly NaN) to trimmed string.

    Handles pandas NaN/None/float safely so that callers never get
    AttributeError when calling .strip().
    """
    if value is None:
        return ""
    try:
        if pd.isna(value):  # type: ignore[arg-type]
            return ""
    except Exception:
        # If pd.isna fails for some exotic type, fall back to str
        pass
    return str(value).strip()


def _find_excel_path() -> Path:
    """Return path to clients Excel file under uploads/.

    Tries clients.xlsx first, then clients.xls.
    Raises FileNotFoundError if none exists.
    """
    uploads_dir = Path("uploads")
    candidates = [uploads_dir / "clients.xlsx", uploads_dir / "clients.xls"]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        "לא נמצא קובץ clients.xlsx או clients.xls בתיקיית uploads/"
    )


def load_clients_dataframe(path: Path) -> pd.DataFrame:
    """Load Excel into a DataFrame with all values as strings."""
    df = pd.read_excel(path, dtype=str)
    # Normalize column names to simple ascii where possible
    df.columns = [c.strip() for c in df.columns]
    return df


def import_client_details(df: pd.DataFrame) -> None:
    """Update client and client_details tables from DataFrame.

    Only updates existing clients (by ID column) and only fills
    fields that are currently NULL or empty.
    """

    columns = set(df.columns)

    # Detect ID column: support both internal name and Hebrew Excel headers
    id_candidates = [
        "id_canon",  # internal / english
        "תז",
        "ת.ז",
        "ת. ז",
        "תז.",
        "ת.ז.",
    ]
    id_col = None
    for cand in id_candidates:
        if cand in columns:
            id_col = cand
            break

    if not id_col:
        raise ValueError("הקובץ חייב להכיל עמודה עם מספר ת.ז. (id_canon או תז)")

    # Optional columns we know how to handle – map logical names to actual
    field_candidates = {
        "first_name": ["first_name", "פרטי"],
        "last_name": ["last_name", "משפחה"],
        "phone": ["phone", "טלפון"],
        "email": ["email", "דואל", "אימייל", "מייל"],
        "employer": ["employer", "מעסיק"],
        "date_of_birth": ["date_of_birth", "ת לידה", "תאריך לידה"],
        "gender": ["gender", "מין"],
        "marital_status": ["marital_status", "סטטוס", "מצב משפחתי"],
        "birth_country": ["birth_country", "ארץ לידה"],
        "street": ["street", "רחוב"],
        "house_number": ["house_number", "מספר", "מספר בית"],
        "city": ["city", "עיר"],
        "employer_address": ["employer_address", "כתובת מעסיק"],
        "employer_phone": ["employer_phone", "טלפון מעסיק"],
        "employer_hp": ["employer_hp", "חפ מעסיק", "ח.פ מעסיק"],
    }

    excel_cols: dict[str, str] = {}
    for logical_name, candidates in field_candidates.items():
        for cand in candidates:
            if cand in columns:
                excel_cols[logical_name] = cand
                break

    with sqlite3.connect(DB) as con:
        cur = con.cursor()

        updated_clients = 0
        updated_details = 0
        skipped_missing = 0

        for _, row in df.iterrows():
            raw_id = row.get(id_col)
            id_canon = _normalize_id(raw_id)
            if not id_canon:
                skipped_missing += 1
                continue

            client_row = cur.execute(
                "SELECT id, first_name, last_name, phone, email, street, house_number, city FROM client WHERE id_canon = ?",
                (id_canon,),
            ).fetchone()
            if not client_row:
                # Client does not exist in DB, skip quietly
                skipped_missing += 1
                continue

            client_id, cur_first, cur_last, cur_phone, cur_email, cur_street, cur_house_number, cur_city = (
                client_row[0],
                client_row[1] or "",
                client_row[2] or "",
                client_row[3] or "",
                client_row[4] or "",
                client_row[5] or "",
                client_row[6] or "",
                client_row[7] or "",
            )

            # Prepare updates for client table but do not overwrite non-empty values
            client_updates = []
            client_params = []

            new_first = ""
            if "first_name" in excel_cols:
                new_first = _cell_to_str(row.get(excel_cols["first_name"]))
            if new_first and not cur_first:
                client_updates.append("first_name = ?")
                client_params.append(new_first)

            new_last = ""
            if "last_name" in excel_cols:
                new_last = _cell_to_str(row.get(excel_cols["last_name"]))
            if new_last and not cur_last:
                client_updates.append("last_name = ?")
                client_params.append(new_last)

            new_phone = ""
            if "phone" in excel_cols:
                new_phone = _cell_to_str(row.get(excel_cols["phone"]))
            if new_phone and not cur_phone:
                client_updates.append("phone = ?")
                client_params.append(new_phone)

            new_email = ""
            if "email" in excel_cols:
                new_email = _cell_to_str(row.get(excel_cols["email"]))
            if new_email and not cur_email:
                client_updates.append("email = ?")
                client_params.append(new_email)

            # Address fields on client table
            new_street = ""
            if "street" in excel_cols:
                new_street = _cell_to_str(row.get(excel_cols["street"]))
            if new_street and not cur_street:
                client_updates.append("street = ?")
                client_params.append(new_street)

            new_house_number = ""
            if "house_number" in excel_cols:
                new_house_number = _cell_to_str(row.get(excel_cols["house_number"]))
            if new_house_number and not cur_house_number:
                client_updates.append("house_number = ?")
                client_params.append(new_house_number)

            new_city = ""
            if "city" in excel_cols:
                new_city = _cell_to_str(row.get(excel_cols["city"]))
            if new_city and not cur_city:
                client_updates.append("city = ?")
                client_params.append(new_city)

            if client_updates:
                client_params.append(client_id)
                cur.execute(
                    f"UPDATE client SET {', '.join(client_updates)} WHERE id = ?",
                    client_params,
                )
                updated_clients += 1

            # Build row dict for client_details upsert
            details_row = {}

            if "first_name" in excel_cols:
                details_row["first_name"] = new_first
            if "last_name" in excel_cols:
                details_row["last_name"] = new_last
            if "email" in excel_cols:
                details_row["email"] = new_email
            if "employer" in excel_cols:
                details_row["employer"] = _cell_to_str(row.get(excel_cols["employer"]))

            if "date_of_birth" in excel_cols:
                raw_dob = _cell_to_str(row.get(excel_cols["date_of_birth"]))
                if raw_dob:
                    # Try to normalize to YYYY-MM-DD; if fails, keep original string
                    try:
                        parsed = datetime.fromisoformat(raw_dob)
                        details_row["date_of_birth"] = parsed.strftime("%Y-%m-%d")
                    except Exception:
                        details_row["date_of_birth"] = raw_dob

            # Extra personal/employment fields (client_details)
            if "gender" in excel_cols:
                details_row["gender"] = _cell_to_str(row.get(excel_cols["gender"]))
            if "marital_status" in excel_cols:
                details_row["marital_status"] = _cell_to_str(row.get(excel_cols["marital_status"]))
            if "birth_country" in excel_cols:
                details_row["birth_country"] = _cell_to_str(row.get(excel_cols["birth_country"]))
            if "employer_address" in excel_cols:
                details_row["employer_address"] = _cell_to_str(row.get(excel_cols["employer_address"]))
            if "employer_phone" in excel_cols:
                details_row["employer_phone"] = _cell_to_str(row.get(excel_cols["employer_phone"]))
            if "employer_hp" in excel_cols:
                details_row["employer_hp"] = _cell_to_str(row.get(excel_cols["employer_hp"]))

            if details_row:
                upsert_client_details(con, client_id, details_row)
                updated_details += 1

        con.commit()

    print(f"Updated {updated_clients} client rows.")
    print(f"Updated/inserted client_details for {updated_details} clients.")
    print(f"Skipped {skipped_missing} rows (missing ID or client not found in DB).")


def main() -> None:
    excel_path = _find_excel_path()
    print(f"טוען פרטי לקוחות מהקובץ: {excel_path}")
    df = load_clients_dataframe(excel_path)
    import_client_details(df)


if __name__ == "__main__":
    main()
