import types
import pandas as pd
import pytest

from services.upload_service import (
    get_loader_for_filename,
    transform_uploaded_file,
    UploadProcessingError,
)


def _assert_loader(result, expected_type):
    load_fn, file_type = result
    if expected_type is None:
        assert load_fn is None
        assert file_type is None
    else:
        assert isinstance(load_fn, types.FunctionType)
        assert file_type == expected_type


def test_get_loader_for_known_types_basic():
    _assert_loader(get_loader_for_filename("report_yl_2025.xlsx"), "YL")
    _assert_loader(get_loader_for_filename("fnx_positions.xls"), "FNX")
    _assert_loader(get_loader_for_filename("mor_data.xlsx"), "MOR")
    _assert_loader(get_loader_for_filename("analysis_anlst.xlsx"), "ANLST")
    _assert_loader(get_loader_for_filename("nfty_snapshot.xlsx"), "NFTY")
    _assert_loader(get_loader_for_filename("as_report.xlsx"), "AS")


def test_get_loader_for_dash_and_ds():
    _assert_loader(get_loader_for_filename("dash_export.xlsx"), "DASH")
    _assert_loader(get_loader_for_filename("DS_2025_10.xlsx"), "DASH")
    _assert_loader(get_loader_for_filename("client_ds_positions.xls"), "DASH")


def test_get_loader_for_unknown_file():
    _assert_loader(get_loader_for_filename("unknown_provider.xlsx"), None)


def test_transform_uploaded_file_empty_df_raises():
    """Empty DataFrame should raise a user-facing UploadProcessingError."""
    empty_df = pd.DataFrame()
    with pytest.raises(UploadProcessingError) as exc:
        transform_uploaded_file(empty_df, "report_yl_2025.xlsx", "2025-01-01")
    assert "הקובץ ריק" in exc.value.user_message


def test_transform_uploaded_file_unsupported_file_raises():
    """Unsupported filename should raise UploadProcessingError about file type."""
    df = pd.DataFrame({"A": [1]})
    with pytest.raises(UploadProcessingError) as exc:
        transform_uploaded_file(df, "unknown_provider.xlsx", "2025-01-01")
    assert "סוג קובץ לא נתמך" in exc.value.user_message


def test_transform_uploaded_file_invalid_date_raises():
    """Invalid snapshot date format should raise UploadProcessingError."""
    # Non-empty DataFrame with a known filename so loader resolution succeeds
    df = pd.DataFrame({"client_name": ["x"], "id_canon": ["1"], "accumulated_amount": [10]})
    with pytest.raises(UploadProcessingError) as exc:
        transform_uploaded_file(df, "mor_data.xlsx", "2025/01/01")
    assert "תאריך סנפשוט" in exc.value.user_message
