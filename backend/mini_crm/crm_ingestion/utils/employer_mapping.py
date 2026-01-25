"""
Employer mapping utilities for Mini CRM
Maps source codes to default employer names
"""

# מיפוי קודי מקור לשמות מעסיקים ברירת מחדל
EMPLOYER_MAPPING = {
    "AS": "אלטשולר-שחם",
    "ANLST": "אנליסט",
    "YL": "ילין לפידות",
    "DASH": "מיטב-דש",
    "FNX": "הפניקס",
    "MOR": "מור",
    "NFTY": "אינפיניטי"
}

def get_default_employer(source_code: str) -> str:
    """
    Get default employer name for a source code
    
    Args:
        source_code: The source code (e.g., "AS", "ANLST")
        
    Returns:
        The default employer name or empty string if not found
    """
    if not source_code or not isinstance(source_code, str):
        return ""
    
    # Normalize source code to uppercase for consistent lookup
    normalized_code = source_code.upper()
    
    # Return mapped employer or empty string if not found
    return EMPLOYER_MAPPING.get(normalized_code, "")
