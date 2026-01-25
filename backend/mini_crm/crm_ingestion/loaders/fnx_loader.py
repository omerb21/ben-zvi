# crm_ingestion/loaders/fnx_loader.py
import pandas as pd
import logging
from crm_ingestion.utils.normalize import normalize_id, normalize_name, create_client_key
from crm_ingestion.utils.fund_utils import detect_fund_type

logger = logging.getLogger(__name__)

COLUMN_MAP = {
    "שם קופה": "fund_name",           # שם קופה
    "שם עמית": "client_name",         # שם העמית (שם + משפחה)
    "ת.ז. עמית": "id_canon",          # ת״ז העמית
    "מספר חשבון": "fund_number",       # מספר קופה אישי
    # "מספר חשבון קודם": מתעלמים
    "מעמד": "fund_type",               # מעמד (שכיר / עצמאי) – אם רוצים לשמור
    # "תאריך הצטרפות": מתעלמים
    # "תאריך נכונות היתרה": מתעלמים, snapshot_date יגיע מה‑CLI
    "יתרה ב₪": "accumulated_amount",    # יתרה
}

REQUIRED_COLS = ["fund_name", "client_name", "id_canon",
                 "fund_number", "accumulated_amount"]

def load_and_transform(df: pd.DataFrame, snapshot_date: str) -> pd.DataFrame:
    """ממפה ומחזיר DataFrame מוכן להכנסה לבסיס‑הנתונים."""
    logger.debug(f"FNX loader: Processing {len(df)} rows")
    
    # מיפוי עמודות לפי אינדקס
    df = df.rename(columns=COLUMN_MAP)
    
    # שמירה רק על העמודות הרלוונטיות
    relevant_cols = [col for col in COLUMN_MAP.values() if col in df.columns]
    df = df[relevant_cols]
    
    # בדיקת עמודות חובה
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in FNX file: {missing}")
    
    # הוספת שדות נוספים
    df["snapshot_date"] = snapshot_date
    df["source"] = "FNX"
    
    # קביעת סוג המוצר לפי שם המסלול
    df["fund_type"] = df["fund_name"].apply(detect_fund_type)
    
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
    df["date_of_birth"] = None  # FNX לא מכיל תאריך לידה
    df["email"] = None  # FNX לא מכיל אימייל
    df["employer"] = get_default_employer("FNX")  # מעסיק ברירת מחדל
    
    # ניקוי נתונים - הסרת שורות עם ערכים חסרים בשדות חובה
    initial_count = len(df)
    df = df.dropna(subset=REQUIRED_COLS)
    
    # המרת יתרה למספר וסינון יתרות 0 או שליליות
    from crm_ingestion.utils.normalize import clean_amount
    df["accumulated_amount"] = df["accumulated_amount"].apply(clean_amount)
    df = df.dropna(subset=["accumulated_amount"])
    df = df[df["accumulated_amount"] > 0]
    
    final_count = len(df)
    
    if initial_count != final_count:
        logger.warning(f"FNX loader: Dropped {initial_count - final_count} rows with missing data or zero amounts")
    
    logger.debug(f"FNX loader: Successfully processed {final_count} rows")
    return df
