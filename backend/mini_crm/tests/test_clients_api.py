"""Integration tests for client update/delete API routes.

Uses a temporary SQLite DB and the real app factory, similar to other tests.
"""
import pytest
import tempfile
import os
import sqlite3
import pandas as pd
from pathlib import Path
import sys

# Add the parent directory to the path so we can import from the project
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, init_db, insert_rows


@pytest.fixture
def app():
    """Create and configure a test app for client API tests."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    app = create_app()
    app.config["TESTING"] = True
    app.config["DB"] = db_path

    with app.app_context():
        # Override the DB constant temporarily
        import app as app_module
        original_db = app_module.DB
        app_module.DB = db_path

        # Initialize the test database
        init_db()

        # Insert some test data so that clients exist
        test_data = pd.DataFrame(
            {
                "client_name": ["בדיקה יוסף", "שרה כהן"],
                "id_canon": ["123456789", "987654321"],
                "fund_number": ["TEST-001", "TEST-002"],
                "fund_code": ["TST001", "TST002"],
                "fund_type": ["מניות", "אגח"],
                "fund_name": ["קרן בדיקה 1", "קרן בדיקה 2"],
                "accumulated_amount": [10000.0, 5000.0],
                "client_key": ["בדיקה יוסף_123456789", "שרה כהן_987654321"],
            }
        )

        insert_rows(test_data, source="TEST", snap_date="2025-07-01")

        # Restore original DB
        app_module.DB = original_db

    yield app

    # Clean up
    try:
        os.unlink(db_path)
    except Exception:
        pass


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


def test_update_client_success(client, app):
    """Updating an existing client should succeed and persist changes."""
    payload = {
        "first_name": "יוסי",
        "last_name": "בדיקה",
        "phone": "050-1234567",
        "email": "test@example.com",
        "street": "רחוב הבדיקה",
        "house_number": "10",
        "city": "תל אביב",
    }

    res = client.post("/client/123456789/update", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data is not None
    assert data.get("ok") is True

    # Verify DB was updated
    db_path = app.config["DB"]
    with sqlite3.connect(db_path) as con:
        row = con.execute(
            "SELECT first_name, last_name, phone, email, street, house_number, city FROM client WHERE id_canon = ?",
            ("123456789",),
        ).fetchone()

    assert row is not None
    assert row[0] == payload["first_name"]
    assert row[1] == payload["last_name"]
    assert row[2] == payload["phone"]
    assert row[3] == payload["email"]
    assert row[4] == payload["street"]
    assert row[5] == payload["house_number"]
    assert row[6] == payload["city"]


def test_update_client_not_found(client):
    """Updating a non-existent client should return 404."""
    payload = {"first_name": "מישהו"}
    res = client.post("/client/000000000/update", json=payload)
    assert res.status_code == 404
    data = res.get_json()
    assert data is not None
    assert data.get("ok") is False


def test_delete_client_success(client, app):
    """Deleting an existing client should remove it from the DB."""
    # Ensure client exists before deletion
    db_path = app.config["DB"]
    with sqlite3.connect(db_path) as con:
        row = con.execute(
            "SELECT id FROM client WHERE id_canon = ?",
            ("123456789",),
        ).fetchone()
    assert row is not None

    res = client.post("/client/123456789/delete")
    assert res.status_code == 200
    data = res.get_json()
    assert data is not None
    assert data.get("ok") is True

    # Verify client was deleted
    with sqlite3.connect(db_path) as con:
        row_after = con.execute(
            "SELECT id FROM client WHERE id_canon = ?",
            ("123456789",),
        ).fetchone()
    assert row_after is None


def test_delete_client_not_found(client):
    """Deleting a non-existent client should return 404."""
    res = client.post("/client/000000000/delete")
    assert res.status_code == 404
    data = res.get_json()
    assert data is not None
    assert data.get("ok") is False
