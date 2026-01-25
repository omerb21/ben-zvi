"""
Source name mapping utilities for Mini CRM
"""

# מיפוי קודי מקור לשמות יצרנים בעברית
SOURCE_DISPLAY_NAMES = {
    "AS": "אלטשולר-שחם",
    "ANLST": "אנליסט",
    "YL": "ילין לפידות",
    "DASH": "מיטב-דש",
    "FNX": "הפניקס",
    "MOR": "מור",
    "NFTY": "אינפיניטי"
}

def get_source_display_name(source_code):
    """
    Get the Hebrew display name for a source code
    
    Args:
        source_code: The source code (e.g., "AS", "ANLST")
        
    Returns:
        The Hebrew display name or the original code if not found
    """
    # Normalize source code to uppercase for consistent lookup
    normalized_code = source_code.upper() if isinstance(source_code, str) else ""
    
    # Return mapped name or original if not found
    return SOURCE_DISPLAY_NAMES.get(normalized_code, source_code)
