"""
Loader for Infinity – NFTY Excel files.
Columns (0‑based):
 0  תעודת זהות                    → id_canon
 1  מס עמית/נעמן                  → fund_number   (a.k.a "מספר קופה")
 2  [ignore]
 3  שם עמית/חברה                  → client_name   (first + last)
 4  [ignore]
 5  יתרת שיערוך                   → accumulated_amount
 6+ [ignore]

Constant additions:
  fund_type      = ""        # אין מידע
  fund_name      = "אינפינטי"
  fund_code      = ""        # לא רלוונטי במקור
  snapshot_date  = passed‑in arg
  source         = "NFTY"
"""

import pandas as pd
from datetime import datetime, date
from crm_ingestion.utils.normalize import (
    normalize_id,
    normalize_name,
    create_client_key,
    clean_amount,
)


COLUMN_MAP = {
    "מס' ת.ז/חפ": "id_canon",
    "מס עמית/נעמן": "fund_number",
    "שם עמית/חברה": "client_name",
    "יתרת שיערוך": "accumulated_amount",
}


REQUIRED = {"id_canon", "client_name", "fund_number", "accumulated_amount"}


def load_and_transform(path_or_df, snapshot_date=None) -> pd.DataFrame:
    """
    Load and transform NFTY Excel file to standardized format
    
    Args:
        path_or_df: Path to Excel file or pandas DataFrame
        snapshot_date: Optional snapshot date (string or date object)
        
    Returns:
        Transformed DataFrame with standardized columns
    """
    # Handle different input types
    if isinstance(path_or_df, str):
        df = pd.read_excel(path_or_df, dtype=str)
        print(f"Loaded NFTY file: {path_or_df}")
    else:
        df = path_or_df.copy()
        print("Processing NFTY DataFrame")
    
    print(f"Raw data shape: {df.shape}")
    print(f"Columns found: {list(df.columns)}")
    
    # Convert snapshot_date to proper format if it's a string
    if isinstance(snapshot_date, str):
        snapshot_date = datetime.strptime(snapshot_date, "%Y-%m-%d").date()
    elif snapshot_date is None:
        snapshot_date = date.today()
    
    # Check for required columns before mapping
    missing_cols = [col for col in COLUMN_MAP.keys() if col not in df.columns]
    if missing_cols:
        print(f"Warning: Missing expected columns: {missing_cols}")
        # Try to find similar column names
        for missing_col in missing_cols:
            similar_cols = [c for c in df.columns if missing_col.replace(" ", "") in str(c).replace(" ", "")]
            if similar_cols:
                print(f"Found similar column '{similar_cols[0]}' for '{missing_col}'")
                df.rename(columns={similar_cols[0]: missing_col}, inplace=True)
    
    # 1. שמות עמודות מסודרים
    df = df.rename(columns=COLUMN_MAP)
    
    # Verify all required columns are present after mapping
    missing_after_mapping = [col for col in COLUMN_MAP.values() if col not in df.columns]
    if missing_after_mapping:
        raise ValueError(f"Missing required columns in NFTY file after mapping: {missing_after_mapping}")

    # 2. שמירת עמודות מעניינות בלבד
    df = df[list(COLUMN_MAP.values())].copy()

    # 3. השלמות מידע קבוע
    df["fund_name"] = "אינפינטי"
    df["fund_code"] = ""
    df["fund_type"] = "לא זמין"  # Set default fund type
    df["snapshot_date"] = snapshot_date.strftime("%Y-%m-%d")
    df["source"] = "NFTY"

    # 4. ניקוי ערכים
    print("Applying canonicalization...")
    df["id_canon"] = df["id_canon"].apply(lambda x: normalize_id(str(x)) if pd.notna(x) else "")
    df["client_name"] = df["client_name"].apply(lambda x: normalize_name(str(x)) if pd.notna(x) else "")
    df["accumulated_amount"] = df["accumulated_amount"].apply(clean_amount)

    # 5. סינון שורות חסרות / אפס
    initial_count = len(df)
    df = df.dropna(subset=list(REQUIRED))
    df = df[df["id_canon"].str.strip() != ""]
    df = df[df["client_name"].str.strip() != ""]
    df = df[df["fund_number"].str.strip() != ""]
    df = df[df["accumulated_amount"] > 0]
    
    final_count = len(df)
    if initial_count != final_count:
        print(f"Removed {initial_count - final_count} rows with missing critical data or zero amounts")

    # 6. מפתח קאנוני
    df["client_key"] = df.apply(
        lambda r: create_client_key(r["client_name"], r["id_canon"]), axis=1
    )
    
    # 6.5. העשרת נתונים עבור client_details
    from crm_ingestion.utils.name_utils import split_full_name
    from crm_ingestion.utils.employer_mapping import get_default_employer
    
    # פיצול שם מלא לשם פרטי ומשפחה
    name_splits = df["client_name"].apply(split_full_name)
    df["first_name"] = [split[0] for split in name_splits]
    df["last_name"] = [split[1] for split in name_splits]
    
    # הוספת שדות נוספים עבור client_details
    df["date_of_birth"] = None  # NFTY לא מכיל תאריך לידה
    df["email"] = None  # NFTY לא מכיל אימייל
    df["employer"] = get_default_employer("NFTY")  # מעסיק ברירת מחדל

    # סדר סופי
    ordered = [
        "client_name",
        "id_canon",
        "fund_number",
        "fund_code",
        "fund_type",
        "fund_name",
        "accumulated_amount",
        "snapshot_date",
        "source",
        "client_key",
    ]
    
    print(f"Transformed data shape: {df.shape}")
    print(f"Unique clients: {df['id_canon'].nunique()}")
    print(f"Sample client keys: {df['client_key'].head(3).tolist()}")
    
    return df[ordered]


if __name__ == "__main__":
    # Test the loader
    import sys
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        snap_date = date.today() if len(sys.argv) < 3 else None
        if len(sys.argv) >= 3:
            snap_date = datetime.strptime(sys.argv[2], "%Y-%m-%d").date()
        
        try:
            df = load_and_transform(file_path, snap_date)
            print(f"\nSuccessfully processed NFTY file:")
            print(f"- {len(df)} records")
            print(f"- {df['id_canon'].nunique()} unique clients")
            print(f"- Snapshot date: {snap_date}")
            print(f"\nFirst few records:")
            print(df.head())
        except Exception as e:
            print(f"Error processing NFTY file: {e}")
            sys.exit(1)
