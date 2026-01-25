"""Integration tests for the /upload/ endpoint."""
import io
import os
import sqlite3
import tempfile
from pathlib import Path

import pandas as pd
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, init_db


@pytest.fixture
def app():
    """Create and configure a test app for upload endpoint tests."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    test_app = create_app()
    test_app.config["TESTING"] = True
    test_app.config["DB"] = db_path

    with test_app.app_context():
        # Override the DB constant temporarily
        import app as app_module

        original_db = app_module.DB
        app_module.DB = db_path

        # Initialize the test database schema
        init_db()

        # Restore original DB constant for other tests
        app_module.DB = original_db

    yield test_app

    # Clean up
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def client(app):
    """Test client for the upload endpoint."""
    return app.test_client()


def test_upload_missing_file_returns_400(client):
    """When no file is provided, endpoint should return 400 with clear error."""
    response = client.post("/upload/", data={"snap_date": "2025-08-01"})
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data["error"] == "לא נבחר קובץ"


def test_upload_missing_snapshot_date_returns_400(client):
    """When snapshot date is missing, endpoint should return 400."""
    data = {
        "file": (io.BytesIO(b"dummy"), "test_yl.xlsx"),
    }
    response = client.post("/upload/", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data["error"] == "חסר תאריך סנפשוט"


def test_upload_success_with_stubbed_transform(monkeypatch, app, client):
    """Happy-path upload using a stubbed transform_uploaded_file helper."""
    import app as app_module

    # Stub transform_uploaded_file to avoid depending on real Excel contents
    def fake_transform(df_raw, filename, snap_date):  # pragma: no cover - simple stub
        df = pd.DataFrame(
            {
                "client_name": ["בדיקה"],
                "id_canon": ["123456789"],
                "fund_number": ["FUND001"],
                "fund_code": ["CODE1"],
                "fund_type": ["מניות"],
                "fund_name": ["קופה בדיקה"],
                "accumulated_amount": [1000.0],
            }
        )
        return df, "TEST"

    monkeypatch.setattr(app_module, "transform_uploaded_file", fake_transform)

    data = {
        "snap_date": "2025-08-15",
        "file": (io.BytesIO(b"dummy"), "test_yl.xlsx"),
    }

    response = client.post("/upload/", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    json_data = response.get_json()

    assert json_data["success"] is True
    assert json_data["file_type"] == "TEST"
    assert json_data["rows_inserted"] == 1

    # Verify that one snapshot row was inserted
    from app import DB

    with sqlite3.connect(DB) as con:
        count = con.execute("SELECT COUNT(*) FROM snapshot").fetchone()[0]
        assert count == 1
