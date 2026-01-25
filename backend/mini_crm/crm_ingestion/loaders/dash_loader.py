"""
Loader for DASH (מיטב-דש) Excel files.

קובץ DASH כולל שלושה שדות רלוונטיים בלבד:
- עמודה 1: שם הלקוח (שם משפחה שם פרטי)
- עמודה 2: מס' תעודת זהות  
- עמודה 3: יתרה (מספרי, ייתכן פסיקים/₪)

שדות קבועים:
- fund_number: "לא זמין"
- fund_type: "לא זמין"  
- fund_name: "מיטב-דש"
- fund_code: "" (ריק)
- source: "DASH"
"""

import pandas as pd
from datetime import datetime, date
from crm_ingestion.utils.normalize import (
    normalize_id,
    normalize_name,
    create_client_key,
    clean_amount,
)

REQUIRED_COLS = ["client_name", "id_canon", "accumulated_amount"]


def load_and_transform(path_or_df, snapshot_date=None, *, verbose=False) -> pd.DataFrame:
    """
    Load and transform DASH Excel file to standardized format
    
    Args:
        path_or_df: Path to Excel file or pandas DataFrame
        snapshot_date: Optional snapshot date (string or date object)
        verbose: Print debug information
        
    Returns:
        Transformed DataFrame with standardized columns
    """
    # Handle different input types
    if isinstance(path_or_df, str):
        df = pd.read_excel(path_or_df, dtype=str)
        if verbose:
            print(f"Loaded DASH file: {path_or_df}")
    else:
        df = path_or_df.copy()
        if verbose:
            print("Processing DASH DataFrame")
    
    if verbose:
        print(f"Raw data shape: {df.shape}")
        print(f"Columns found: {list(df.columns)}")
    
    # Convert snapshot_date to proper format if it's a string
    if isinstance(snapshot_date, str):
        snapshot_date = datetime.strptime(snapshot_date, "%Y-%m-%d").date()
    elif snapshot_date is None:
        snapshot_date = date.today()
    
    # מיפוי עמודות: תמיכה גם בפורמט DS חדש וגם בפורמט DASH ישן
    columns = list(df.columns)

    # פורמט DS חדש: פירוט קופות עם עמודות בעברית כמו ב-ds.xlsx
    if "שם העמית" in columns and "ת.ז" in columns and "יתרה כוללת ב₪" in columns:
        df = df.rename(
            columns={
                "שם העמית": "client_name",
                "ת.ז": "id_canon",
                "יתרה כוללת ב₪": "accumulated_amount",
                "שם קופה": "fund_name",
                "מס' חשבון": "fund_number",
            }
        )

        keep_cols = ["client_name", "id_canon", "accumulated_amount"]
        if "fund_name" in df.columns:
            keep_cols.append("fund_name")
        if "fund_number" in df.columns:
            keep_cols.append("fund_number")
        df = df[keep_cols].copy()
    else:
        # פורמט DASH ישן: 3 העמודות הראשונות בלבד (יתרה כללית ללא פירוט קופות)
        if len(df.columns) < 3:
            raise ValueError(f"DASH file must have at least 3 columns, found {len(df.columns)}")

        df = df.rename(
            columns={
                df.columns[0]: "client_name",
                df.columns[1]: "id_canon", 
                df.columns[2]: "accumulated_amount",
            }
        )

        # שמירת עמודות רלוונטיות בלבד
        df = df[["client_name", "id_canon", "accumulated_amount"]].copy()
    
    if verbose:
        print(f"After column mapping: {df.shape}")
    
    # ניקוי יתרה - הסרת סימנים מיוחדים (₪, פסיקים, רווחים)
    df["accumulated_amount"] = df["accumulated_amount"].apply(clean_amount)
    
    # נורמליזציה של מזהים ושמות
    if verbose:
        print("Applying canonicalization...")
    
    df["id_canon"] = df["id_canon"].apply(lambda x: normalize_id(str(x)) if pd.notna(x) else "")
    df["client_name"] = df["client_name"].apply(lambda x: normalize_name(str(x)) if pd.notna(x) else "")
    
    # סינון רשומות חסרות או סכום 0
    initial_count = len(df)
    df = df.dropna(subset=REQUIRED_COLS)
    df = df[df["id_canon"].str.strip() != ""]
    df = df[df["client_name"].str.strip() != ""]
    df = df[df["accumulated_amount"] > 0]
    
    final_count = len(df)
    if initial_count != final_count and verbose:
        print(f"Removed {initial_count - final_count} rows with missing critical data or zero amounts")
    
    # שדות קבועים (לא לדרוס אם הקובץ כבר סיפק ערכים מפורטים)
    if "fund_number" not in df.columns:
        df["fund_number"] = "לא זמין"
    if "fund_type" not in df.columns:
        df["fund_type"] = "לא זמין"
    if "fund_name" not in df.columns:
        df["fund_name"] = "מיטב-דש"
    if "fund_code" not in df.columns:
        df["fund_code"] = ""
    df["source"] = "DASH"
    df["snapshot_date"] = snapshot_date.strftime("%Y-%m-%d")
    
    # מפתח קאנוני לאיחוד כפילויות
    df["client_key"] = df.apply(
        lambda r: create_client_key(r["client_name"], r["id_canon"]), axis=1
    )
    
    # העשרת נתונים עבור client_details
    from crm_ingestion.utils.name_utils import split_full_name
    from crm_ingestion.utils.employer_mapping import get_default_employer
    
    # פיצול שם מלא לשם פרטי ומשפחה
    name_splits = df["client_name"].apply(split_full_name)
    df["first_name"] = [split[0] for split in name_splits]
    df["last_name"] = [split[1] for split in name_splits]
    
    # הוספת שדות נוספים עבור client_details
    df["date_of_birth"] = None  # DASH לא מכיל תאריך לידה
    df["email"] = None  # DASH לא מכיל אימייל
    df["employer"] = get_default_employer("DASH")  # מעסיק ברירת מחדל
    
    if verbose:
        print(f"DASH loader: transformed {len(df)} rows")
        print(f"Unique clients: {df['id_canon'].nunique()}")
        print(f"Sample client keys: {df['client_key'].head(3).tolist()}")
    
    # סדר עמודות סופי
    ordered_columns = [
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
    
    return df[ordered_columns]


if __name__ == "__main__":
    # Test the loader
    import sys
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        snap_date = date.today() if len(sys.argv) < 3 else None
        if len(sys.argv) >= 3:
            snap_date = datetime.strptime(sys.argv[2], "%Y-%m-%d").date()
        
        try:
            df = load_and_transform(file_path, snap_date, verbose=True)
            print(f"\nSuccessfully processed DASH file:")
            print(f"- {len(df)} records")
            print(f"- {df['id_canon'].nunique()} unique clients")
            print(f"- Snapshot date: {snap_date}")
            print(f"\nFirst few records:")
            print(df.head())
        except Exception as e:
            print(f"Error processing DASH file: {e}")
            sys.exit(1)
