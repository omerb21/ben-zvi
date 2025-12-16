from datetime import date, datetime
from typing import Optional


def _parse_iso_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def _utc_timestamp_str() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
