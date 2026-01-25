"""
MOR Loader - handles MOR Excel files with dynamic balance column headers
"""
import pandas as pd
import re
from datetime import datetime, date
from typing import Optional
from crm_ingestion.utils.normalize import normalize_id, normalize_name, create_client_key


# Column mapping for MOR files
COLUMN_MAP = {
    "שם העמית": "client_name",
    "זהות": "id_canon", 
    "חשבון": "fund_number",
    "סוג קופה": "fund_type",
    "מסלול": "fund_name"
}

REQUIRED_COLUMNS = list(COLUMN_MAP.keys())


def _find_balance_column(df: pd.DataFrame) -> str:
    """Find the balance column that starts with 'יתרה'"""
    for col in df.columns:
        if str(col).strip().startswith("יתרה"):
            return col
    raise ValueError("Balance column starting with 'יתרה' not found in MOR file")


def _extract_date_from_balance_header(balance_col: str) -> Optional[date]:
    """Extract date from balance column header if it contains DD/MM/YY pattern"""
    # Look for pattern like "יתרה נכון ל-27/07/25" or similar
    match = re.search(r"(\d{2}/\d{2}/\d{2})", balance_col)
    if match:
        try:
            return datetime.strptime(match.group(1), "%d/%m/%y").date()
        except ValueError:
            pass
    return None


def _clean_amount(amount_str) -> float:
    """Clean amount string by removing currency symbols and commas, convert to float"""
    if pd.isna(amount_str):
        return 0.0
    
    # Convert to string and remove non-numeric characters except decimal point
    cleaned = str(amount_str).replace("₪", "").replace(",", "").strip()
    # Remove any other non-numeric characters except digits and decimal point
    cleaned = re.sub(r"[^0-9.]", "", cleaned)
    
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0


def _map_fund_type(fund_type: str) -> str:
    """
    Map specific fund types to standardized values.
    
    Args:
        fund_type: Original fund type from the file
        
    Returns:
        Mapped fund type or original if no mapping exists
    """
    if not fund_type or not isinstance(fund_type, str):
        return fund_type
        
    fund_type = fund_type.strip()
    
    # Map specific fund types
    if fund_type == "אלפא מור תגמולים":
        return "קופת גמל"
    elif fund_type == "מור השתלמות":
        return "קרן השתלמות"
        
    return fund_type


def load_and_transform(file_path_or_df, snapshot_date = None) -> pd.DataFrame:
    """
    Load and transform MOR Excel file to standardized format
    
    Args:
        file_path_or_df: Path to Excel file or pandas DataFrame
        snapshot_date: Optional snapshot date (string or date object), if None will try to extract from balance column header
        
    Returns:
        Transformed DataFrame with standardized columns
    """
    # Convert snapshot_date to date object if it's a string
    if isinstance(snapshot_date, str):
        snapshot_date = datetime.strptime(snapshot_date, "%Y-%m-%d").date()
    # Load the data
    if isinstance(file_path_or_df, str):
        raw_df = pd.read_excel(file_path_or_df)
        print(f"Loaded MOR file: {file_path_or_df}")
    else:
        raw_df = file_path_or_df.copy()
        print("Processing MOR DataFrame")
    
    print(f"Raw data shape: {raw_df.shape}")
    print(f"Columns found: {list(raw_df.columns)}")
    
    # Check for required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in raw_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in MOR file: {missing_cols}")
    
    # Find the balance column
    balance_col = _find_balance_column(raw_df)
    print(f"Found balance column: '{balance_col}'")
    
    # Extract snapshot date from balance column header if not provided
    extracted_date = _extract_date_from_balance_header(balance_col)
    if snapshot_date is None and extracted_date:
        snapshot_date = extracted_date
        print(f"Extracted snapshot date from header: {snapshot_date}")
    elif snapshot_date is None:
        print("Warning: No snapshot date provided and could not extract from header")
        snapshot_date = date.today()
    
    # Start with mapped columns
    df = raw_df[REQUIRED_COLUMNS].copy()
    df = df.rename(columns=COLUMN_MAP)
    
    # Map fund types to standardized values
    if 'fund_type' in df.columns:
        df['fund_type'] = df['fund_type'].apply(_map_fund_type)
    
    # Process the balance column
    df["accumulated_amount"] = raw_df[balance_col].apply(_clean_amount)
    
    # Add metadata columns
    df["snapshot_date"] = snapshot_date.strftime("%Y-%m-%d")
    df["source"] = "MOR"
    df["fund_code"] = ""  # Empty as specified
    
    # Apply canonicalization
    print("Applying canonicalization...")
    df["id_canon"] = df["id_canon"].apply(lambda x: normalize_id(str(x)) if pd.notna(x) else "")
    df["client_name"] = df["client_name"].apply(lambda x: normalize_name(str(x)) if pd.notna(x) else "")
    df["client_key"] = df.apply(lambda row: create_client_key(row["client_name"], row["id_canon"]), axis=1)
    
    # העשרת נתונים עבור client_details
    from crm_ingestion.utils.name_utils import split_full_name
    from crm_ingestion.utils.employer_mapping import get_default_employer
    
    # פיצול שם מלא לשם פרטי ומשפחה
    name_splits = df["client_name"].apply(split_full_name)
    df["first_name"] = [split[0] for split in name_splits]
    df["last_name"] = [split[1] for split in name_splits]
    
    # הוספת שדות נוספים עבור client_details
    df["date_of_birth"] = None  # MOR לא מכיל תאריך לידה
    df["email"] = None  # MOR לא מכיל אימייל
    df["employer"] = get_default_employer("MOR")  # מעסיק ברירת מחדל
    
    # Remove rows with missing critical data
    initial_count = len(df)
    df = df.dropna(subset=["client_name", "id_canon"])
    df = df[df["client_name"].str.strip() != ""]
    df = df[df["id_canon"].str.strip() != ""]
    
    # Filter out zero or negative amounts
    df = df.dropna(subset=["accumulated_amount"])
    df = df[df["accumulated_amount"] > 0]
    
    final_count = len(df)
    if initial_count != final_count:
        print(f"Removed {initial_count - final_count} rows with missing data or zero amounts")
    
    print(f"Transformed data shape: {df.shape}")
    print(f"Unique clients: {df['id_canon'].nunique()}")
    print(f"Sample client keys: {df['client_key'].head(3).tolist()}")
    
    return df


if __name__ == "__main__":
    # Test the loader
    import sys
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        snap_date = date.today() if len(sys.argv) < 3 else datetime.strptime(sys.argv[2], "%Y-%m-%d").date()
        
        try:
            df = load_and_transform(file_path, snap_date)
            print(f"\nSuccessfully processed MOR file:")
            print(f"- {len(df)} records")
            print(f"- {df['id_canon'].nunique()} unique clients")
            print(f"- Snapshot date: {snap_date}")
            print(f"\nFirst few records:")
            print(df.head())
        except Exception as e:
            print(f"Error processing MOR file: {e}")
            sys.exit(1)
