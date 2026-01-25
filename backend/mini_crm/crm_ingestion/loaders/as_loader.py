# crm_ingestion/loaders/as_loader.py
import pandas as pd
import re
import logging
from crm_ingestion.utils.normalize import normalize_id, normalize_name, create_client_key

logger = logging.getLogger(__name__)

COLUMN_MAP = {
    "שם עמית": "client_name",
    "תעודת זהות": "id_canon",  # Updated to match actual column name in AS file
    # שדות להמשך פיתוח (נשמרים בת־מפה אך לא נכתבים): 
    # "תאריך לידה": "birth_date",
    # "דוא\"ל": "email",
    # "טלפון": "phone",
    "יתרה": "accumulated_amount",
}

def clean_amount(val) -> float:
    """הסרת ‎₪ ורווחים, המרת פסיק לנקודה, החזרת float"""
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    # הסרת כל התווים שאינם ספרות, נקודה, פסיק או מינוס
    cleaned = re.sub(r"[^\d.,-]", "", str(val)).replace(",", "")
    try:
        return float(cleaned or 0)
    except ValueError:
        logger.warning(f"Could not convert amount '{val}' to float, using 0.0")
        return 0.0

def load_and_transform(df: pd.DataFrame, snapshot_date: str) -> pd.DataFrame:
    """ממפה ומחזיר DataFrame מוכן להכנסה לבסיס‑הנתונים."""
    logger.debug(f"AS loader: Processing {len(df)} rows")
    
    # מיפוי שמות עמודות
    df = df.rename(columns=COLUMN_MAP)
    
    # סינון לעמודות הרלוונטיות בלבד
    relevant_cols = [col for col in COLUMN_MAP.values() if col in df.columns]
    df = df[relevant_cols]
    
    # ניקוי יתרה
    if "accumulated_amount" in df.columns:
        df["accumulated_amount"] = df["accumulated_amount"].apply(clean_amount)
    
    # עמודות חובה למערכת (שאינן קיימות בקובץ)
    df["fund_number"] = "לא זמין"         # ערך ברירת מחדל למספר קופה
    df["fund_code"] = ""                  # אין קוד קרן
    df["fund_type"] = "לא זמין"           # ערך ברירת מחדל לסוג מוצר
    df["fund_name"] = "אלטשולר שחם"      # ערך ברירת מחדל לשם מסלול
    df["snapshot_date"] = snapshot_date
    df["source"] = "AS"
    
    # קאנוניזציה
    df["id_canon"] = df["id_canon"].apply(normalize_id)
    df["client_key"] = df.apply(lambda row: create_client_key(row["client_name"], row["id_canon"]), axis=1)
    
    # העשרת נתונים עבור client_details
    from crm_ingestion.utils.name_utils import split_full_name
    from crm_ingestion.utils.employer_mapping import get_default_employer
    
    # פיצול שם מלא לשם פרטי ומשפחה
    name_splits = df["client_name"].apply(split_full_name)
    df["first_name"] = [split[0] for split in name_splits]
    df["last_name"] = [split[1] for split in name_splits]
    
    # הוספת שדות נוספים עבור client_details
    df["date_of_birth"] = None  # AS לא מכיל תאריך לידה
    df["email"] = None  # AS לא מכיל אימייל
    df["employer"] = get_default_employer("AS")  # מעסיק ברירת מחדל
    
    # ניקוי נתונים - הסרת שורות עם ערכים חסרים בשדות חובה
    required_cols = ["client_name", "id_canon", "accumulated_amount"]
    initial_count = len(df)
    df = df.dropna(subset=required_cols)
    
    # סינון יתרות 0 או שליליות
    df = df.dropna(subset=["accumulated_amount"])
    df = df[df["accumulated_amount"] > 0]
    
    final_count = len(df)
    
    if initial_count != final_count:
        logger.warning(f"AS loader: Dropped {initial_count - final_count} rows with missing data or zero amounts")
    
    logger.info(f"AS loader: Transformed {final_count} rows from AS data")
    return df
