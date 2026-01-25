"""
YL Data Loader
Handles loading and mapping data from YL Excel files
"""

import logging
import pandas as pd
from crm_ingestion.utils.normalize import normalize_id, normalize_name, create_client_key
from datetime import datetime

logger = logging.getLogger("crm_ingestion.loaders.yl")

# Column mapping for YL source
COLUMN_MAP = {
    "ת.ז": "id_canon",
    "שם עמית": "client_name",
    "חשבון": "fund_number",  # שינוי: מספר חשבון הוא מספר קופה אישי
    "מוצר": "fund_type",
    "שם מסלול": "fund_name",
    "יתרת מסלול": "accumulated_amount",
}

# All columns in the mapping are required
REQUIRED_COLUMNS = set(COLUMN_MAP.keys())

def load_and_transform(df, snapshot_date=None):
    """
    Load and transform data from YL Excel file
    
    Args:
        df (pd.DataFrame): DataFrame with YL data
        snapshot_date (str): Date of the snapshot in YYYY-MM-DD format
        
    Returns:
        pd.DataFrame: Transformed DataFrame ready for database insertion
    """
    logger.info(f"Processing YL data with {len(df)} rows")
    
    # Validate required columns
    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        error_msg = f"Missing required columns: {', '.join(missing_columns)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Map columns according to COLUMN_MAP using DataFrame.rename
    mapped_df = df.rename(columns=COLUMN_MAP)
    
    # Add snapshot_date after rename
    mapped_df["snapshot_date"] = snapshot_date
    mapped_df["source"] = "YL"
    
    # קאנוניזציה
    mapped_df["id_canon"] = mapped_df["id_canon"].apply(normalize_id)
    mapped_df["client_key"] = mapped_df.apply(lambda row: create_client_key(row["client_name"], row["id_canon"]), axis=1)
    
    # העשרת נתונים עבור client_details
    from crm_ingestion.utils.name_utils import split_full_name
    from crm_ingestion.utils.employer_mapping import get_default_employer
    
    # פיצול שם מלא לשם פרטי ומשפחה
    name_splits = mapped_df["client_name"].apply(split_full_name)
    mapped_df["first_name"] = [split[0] for split in name_splits]
    mapped_df["last_name"] = [split[1] for split in name_splits]
    
    # הוספת שדות נוספים עבור client_details
    mapped_df["date_of_birth"] = None  # YL לא מכיל תאריך לידה
    mapped_df["email"] = None  # YL לא מכיל אימייל
    mapped_df["employer"] = get_default_employer("YL")  # מעסיק ברירת מחדל
    
    # Clean and filter accumulated_amount
    from crm_ingestion.utils.normalize import clean_amount
    mapped_df["accumulated_amount"] = mapped_df["accumulated_amount"].apply(clean_amount)
    
    # Filter out rows with zero or negative amounts
    initial_count = len(mapped_df)
    mapped_df = mapped_df.dropna(subset=["accumulated_amount"])
    mapped_df = mapped_df[mapped_df["accumulated_amount"] > 0]
    final_count = len(mapped_df)
    
    if initial_count != final_count:
        logger.info(f"YL loader: Removed {initial_count - final_count} rows with zero/negative amounts")
    
    # Log and handle rows with missing values
    valid_rows = []
    for idx, row in mapped_df.iterrows():
        missing_values = [col for col in mapped_df.columns if pd.isna(row[col])]
        if missing_values:
            logger.debug(f"Row {idx+1} has missing values in columns: {', '.join(missing_values)}")
        valid_rows.append(row)
    
    result_df = pd.DataFrame(valid_rows)
    logger.info(f"Transformed {len(result_df)} rows from YL data")
    return result_df
