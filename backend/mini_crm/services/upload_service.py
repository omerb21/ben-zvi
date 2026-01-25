from typing import Callable, Optional, Tuple

from datetime import datetime
import pandas as pd


class UploadProcessingError(Exception):
    """Domain error for upload processing failures that should be shown to the user."""

    def __init__(self, user_message: str):
        self.user_message = user_message
        super().__init__(user_message)


def get_loader_for_filename(filename_lower: str) -> Tuple[Optional[Callable], Optional[str]]:
    """Return (load_and_transform function, file_type) based on the filename.

    If the filename does not match any known pattern, returns (None, None).
    The actual imports of loaders are done lazily inside this function
    to avoid unnecessary imports on app startup.
    """
    # Normalize just in case the caller forgot
    filename_lower = filename_lower.lower()

    if "yl" in filename_lower:
        from crm_ingestion.loaders.yl_loader import load_and_transform
        return load_and_transform, "YL"
    if "fnx" in filename_lower:
        from crm_ingestion.loaders.fnx_loader import load_and_transform
        return load_and_transform, "FNX"
    if "mor" in filename_lower:
        from crm_ingestion.loaders.mor_loader import load_and_transform
        return load_and_transform, "MOR"
    if "anlst" in filename_lower:
        from crm_ingestion.loaders.anlst_loader import load_and_transform
        return load_and_transform, "ANLST"
    if "nfty" in filename_lower:
        from crm_ingestion.loaders.nfty_loader import load_and_transform
        return load_and_transform, "NFTY"
    # DASH and DS share the same loader
    if "dash" in filename_lower or "ds" in filename_lower:
        from crm_ingestion.loaders.dash_loader import load_and_transform
        return load_and_transform, "DASH"
    if "as" in filename_lower:
        from crm_ingestion.loaders.as_loader import load_and_transform
        return load_and_transform, "AS"

    return None, None


def transform_uploaded_file(
    df_raw: pd.DataFrame, filename: str, snap_date: str
) -> Tuple[pd.DataFrame, str]:
    """Validate and transform uploaded Excel data using the appropriate loader.

    This performs:
    - Basic validation that the Excel file is not empty
    - File-type detection based on the filename
    - Snapshot date validation (YYYY-MM-DD)
    - Calling the appropriate loader and validating that the result is not empty
    """
    if df_raw is None or df_raw.empty:
        raise UploadProcessingError("הקובץ ריק או לא מכיל נתונים")

    # Detect loader by filename
    load_and_transform, file_type = get_loader_for_filename(filename.lower())
    if load_and_transform is None or file_type is None:
        raise UploadProcessingError(f"סוג קובץ לא נתמך: {filename}")

    # Validate snapshot date format and convert to date object (old behavior)
    if isinstance(snap_date, str):
        try:
            snap_date_obj = datetime.strptime(snap_date, "%Y-%m-%d").date()
        except ValueError:
            raise UploadProcessingError("תאריך סנפשוט אינו בפורמט חוקי (YYYY-MM-DD)")
    else:
        snap_date_obj = snap_date

    df = load_and_transform(df_raw, snapshot_date=snap_date_obj)

    if df is None or df.empty:
        raise UploadProcessingError("לא נמצאו רשומות תקינות בקובץ לאחר עיבוד")

    return df, file_type
