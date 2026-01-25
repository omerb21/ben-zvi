"""
ANLST Loader - handles ANLST Excel files with dynamic balance column headers
"""
import pandas as pd
from datetime import date
from crm_ingestion.utils.normalize import (
    normalize_id, normalize_name, create_client_key,
    clean_amount, today_str,
)

SOURCE = "ANLST"

# הכותרות בקובץ - עודכן לפי המבנה האמיתי של הקובץ
# כל שורה מייצגת קופה בודדת עם יתרה אישית
COLUMN_MAP = {
    "ת.ז.": "id_canon",                     # col 1
    "שם העמית": "client_name",              # col 2
    "מס' חשבון חדש": "fund_number",         # using new account number as fund identifier
    "מס' חשבון": "fund_number",             # older header variant
    "מספר חשבון": "fund_number",            # header without apostrophe
    "שם קופה": "fund_name",                 # col for fund name
    "יתרה": "accumulated_amount",           # individual fund balance (not total)
}

BALANCE_COL_INDEX = 9   # עמודה J (0‑based = 9) – הכותרת משתנה ("יתרה נכון ל‑ …")

REQUIRED = ["id_canon", "client_name", "fund_number", "fund_name", "accumulated_amount"]


def load_and_transform(path_or_df, snapshot_date=None) -> pd.DataFrame:
    """
    Load and transform ANLST Excel file to standardized format
    
    Args:
        path_or_df: Path to Excel file or pandas DataFrame
        snapshot_date: Optional snapshot date (string or date object)
        
    Returns:
        Transformed DataFrame with standardized columns
    """
    # Handle different input types
    if isinstance(path_or_df, str):
        df = pd.read_excel(path_or_df, dtype=str)
        print(f"Loaded ANLST file: {path_or_df}")
    else:
        df = path_or_df.copy()
        print("Processing ANLST DataFrame")
    
    print(f"Raw data shape: {df.shape}")
    print(f"Columns found: {list(df.columns)}")
    
    # Convert snapshot_date to proper format if it's a string
    if isinstance(snapshot_date, str):
        from datetime import datetime
        snapshot_date = datetime.strptime(snapshot_date, "%Y-%m-%d").date()
    
    # ANLST structure: each row is an individual fund with its own balance
    # Use "יתרה" (individual fund balance) not "יתרה כוללת" (total balance)
    if "יתרה" not in df.columns:
        raise ValueError("Individual balance column 'יתרה' not found in ANLST file")
    
    print(f"Using individual fund balance column: 'יתרה'")

    # 2. מיפוי שמות קבועים - כל העמודות כבר ממופות ב-COLUMN_MAP
    df.rename(columns=COLUMN_MAP, inplace=True)

    # If the source file does not provide an explicit fund_number column,
    # synthesize one from existing fields so the downstream logic always
    # has a stable fund identifier per row.
    if "fund_number" not in df.columns:
        if "id_canon" in df.columns and "fund_name" in df.columns:
            df["fund_number"] = (
                df["id_canon"].astype(str).str.strip()
                + "-"
                + df["fund_name"].astype(str).str.strip()
            )
        else:
            # Fallback: use the row index as a last-resort identifier
            df["fund_number"] = df.index.astype(str)

    # Check for required columns after mapping (use unique REQUIRED list
    # instead of raw COLUMN_MAP values to avoid duplicate 'fund_number')
    required_cols = REQUIRED
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in ANLST file after mapping: {missing_cols}")

    # 3. ניקוי ו‑select של העמודות הנחוצות
    df = df[required_cols].copy()

    # 4. נורמליזציה
    df["id_canon"] = df["id_canon"].apply(lambda x: normalize_id(str(x)) if pd.notna(x) else "")
    
    # הופך "פוקס ארנון" → "ארנון פוקס" (reverse name order)
    df["client_name"] = df["client_name"].apply(
        lambda n: normalize_name(" ".join(reversed(str(n).split()))) if pd.notna(n) else ""
    )

    df["accumulated_amount"] = df["accumulated_amount"].apply(clean_amount)

    # 5. Extract fund_type from fund_name (text after last hyphen)
    df["fund_type"] = df["fund_name"].apply(
        lambda x: x.split("-")[-1].strip() if pd.notna(x) and "-" in x else "לא זמין"
    )
    
    # 6. שדות מערכת
    df["fund_code"] = ""                # אין בקובץ
    df["snapshot_date"] = snapshot_date.strftime("%Y-%m-%d") if snapshot_date else today_str()
    df["source"] = SOURCE
    
    # 6.5. העשרת נתונים עבור client_details
    from crm_ingestion.utils.name_utils import split_full_name
    from crm_ingestion.utils.employer_mapping import get_default_employer
    
    # פיצול שם מלא לשם פרטי ומשפחה
    name_splits = df["client_name"].apply(split_full_name)
    df["first_name"] = [split[0] for split in name_splits]
    df["last_name"] = [split[1] for split in name_splits]
    
    # הוספת שדות נוספים עבור client_details
    df["date_of_birth"] = None  # ANLST לא מכיל תאריך לידה
    df["email"] = None  # ANLST לא מכיל אימייל
    df["employer"] = get_default_employer("ANLST")  # מעסיק ברירת מחדל

    # 6. drop rows עם נתונים חסרים
    initial_count = len(df)
    df = df.dropna(subset=["id_canon", "client_name", "fund_number", "accumulated_amount"])
    df = df[df["id_canon"].str.strip() != ""]
    df = df[df["client_name"].str.strip() != ""]
    df = df[df["fund_number"].str.strip() != ""]
    # Remove rows with zero or negative amounts
    df = df[df["accumulated_amount"] > 0]
    
    final_count = len(df)
    if initial_count != final_count:
        print(f"Removed {initial_count - final_count} rows with missing critical data or zero amounts")

    # 7. client_key לקאנוניזציה
    df["client_key"] = df.apply(
        lambda r: create_client_key(r["client_name"], r["id_canon"]),
        axis=1,
    )
    
    print(f"Transformed data shape: {df.shape}")
    print(f"Unique clients: {df['id_canon'].nunique()}")
    print(f"Sample client keys: {df['client_key'].head(3).tolist()}")
    
    return df


if __name__ == "__main__":
    # Test the loader
    import sys
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        snap_date = date.today() if len(sys.argv) < 3 else None
        if len(sys.argv) >= 3:
            from datetime import datetime
            snap_date = datetime.strptime(sys.argv[2], "%Y-%m-%d").date()
        
        try:
            df = load_and_transform(file_path, snap_date)
            print(f"\nSuccessfully processed ANLST file:")
            print(f"- {len(df)} records")
            print(f"- {df['id_canon'].nunique()} unique clients")
            print(f"- Snapshot date: {snap_date}")
            print(f"\nFirst few records:")
            print(df.head())
        except Exception as e:
            print(f"Error processing ANLST file: {e}")
            sys.exit(1)
