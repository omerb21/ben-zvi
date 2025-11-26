SOURCE_DISPLAY_NAMES = {
    "AS": "אלטשולר-שחם",
    "ANLST": "אנליסט",
    "YL": "ילין לפידות",
    "DASH": "מיטב-דש",
    "FNX": "הפניקס",
    "MOR": "מור",
    "NFTY": "אינפיניטי",
}


def get_source_display_name(source_code: str) -> str:
    normalized = source_code.upper() if isinstance(source_code, str) else ""
    return SOURCE_DISPLAY_NAMES.get(normalized, source_code)
