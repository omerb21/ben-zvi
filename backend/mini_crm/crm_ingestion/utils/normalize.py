# crm_ingestion/utils/normalize.py
import re
import unicodedata

# --- ת"ז -----------------------------------------------------------
def normalize_id(id_raw) -> str:
    """
    • מסיר כל תו שאינו ספרה
    • קוצץ אפסים *מובילים*
    • קוצץ אפסים *סופיים* אם מספר הספרות גדול מ‑7
      (‑– ב‑AS/FNX האפס המיותר תמיד מודבק בסוף)
    """
    if id_raw is None:
        return ""
    s = re.sub(r"\D", "", str(id_raw))      # רק ספרות
    s = s.lstrip("0")                       # אפסים מובילים
    
    # אם יש יותר מ-8 ספרות, הסר אפסים סופיים עד שנגיע ל-7-8 ספרות
    # או עד שלא נשארו יותר אפסים בסוף
    while len(s) > 8 and s.endswith("0"):
        s = s[:-1]
    
    # טיפול מיוחד: אם יש בדיוק 8 ספרות ומסתיים באפס/ים,
    # ויש לנו מקרה שנראה כמו ID עם אפס מיותר (כמו 51613020 -> 5161302)
    if len(s) == 8 and s.endswith("0"):
        # בדוק אם הסרת האפס האחרון נותנת ID הגיוני (7 ספרות)
        candidate = s[:-1]
        if len(candidate) == 7:
            s = candidate
    
    return s

# --- שם -----------------------------------------------------------
def normalize_name(name: str) -> str:
    """
    הופך את השם לייצוג אחיד לצורך השוואה בלבד:
    • מסיר ניקוד ו־diacritics
    • מוריד רווחים מיותרים
    • ממיין רכיבי שם (תווים עבריים בלבד) אלפביתית
    """
    if not name or not isinstance(name, str):
        return ""
    
    # הסרת ניקוד
    name = unicodedata.normalize("NFKD", name)
    name = "".join(ch for ch in name if not unicodedata.combining(ch))
    
    # רווחים כפולים → יחיד
    parts = re.sub(r"\s+", " ", name.strip()).split(" ")
    
    # מיון – עושה את "ארנון שלמה" == "שלמה ארנון"
    parts_sorted = sorted(parts)
    return " ".join(parts_sorted)

def clean_amount(amount_str) -> float:
    """
    ניקוי סכום - מסיר סמלי מטבע, פסיקים ותווים לא רלוונטיים
    """
    if amount_str is None or str(amount_str).strip() == "":
        return 0.0
    
    # המרה למחרוזת והסרת תווים לא רלוונטיים
    cleaned = str(amount_str).replace("₪", "").replace(",", "").strip()
    # הסרת כל התווים שאינם ספרות או נקודה עשרונית
    cleaned = re.sub(r"[^0-9.]", "", cleaned)
    
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0


def today_str() -> str:
    """
    מחזיר תאריך היום בפורמט YYYY-MM-DD
    """
    from datetime import date
    return date.today().strftime("%Y-%m-%d")


def create_client_key(name: str, id_canon: str) -> str:
    """
    יוצר מפתח ייחודי ללקוח על בסיס שם מנורמל + ת"ז מנורמלת
    """
    normalized_name = normalize_name(name)
    normalized_id = normalize_id(id_canon)
    return f"{normalized_name}|{normalized_id}"
