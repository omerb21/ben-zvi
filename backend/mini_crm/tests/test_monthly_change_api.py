"""Integration tests for the /api/monthly_change endpoint."""
import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, init_db


@pytest.fixture
def app():
    """Create and configure a test app for monthly change API tests."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    test_app = create_app()
    test_app.config["TESTING"] = True
    test_app.config["DB"] = db_path

    with test_app.app_context():
        import app as app_module

        original_db = app_module.DB
        app_module.DB = db_path

        init_db()

        # Insert sample data for three months
        with sqlite3.connect(db_path) as con:
            # One client
            con.execute(
                "INSERT INTO client (id_canon, name) VALUES (?, ?)",
                ("123456789", "Test Client"),
            )
            client_id = con.execute("SELECT id FROM client WHERE id_canon=?", ("123456789",)).fetchone()[0]

            # Three months of snapshot data
            snapshots = [
                (client_id, "FUND1", 10000.0, "2025-01-01"),
                (client_id, "FUND1", 15000.0, "2025-02-01"),
                (client_id, "FUND1", 12000.0, "2025-03-01"),
            ]
            for cid, fund_number, amount, snap_date in snapshots:
                con.execute(
                    """
                    INSERT INTO snapshot (
                        client_id, fund_code, fund_number, fund_type, fund_name,
                        snapshot_date, amount, source, company, is_active
                    ) VALUES (?, '', ?, '', '', ?, ?, 'TEST', '', 1)
                    """,
                    (cid, fund_number, snap_date, amount),
                )

        app_module.DB = original_db

    yield test_app

    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def client(app):
    return app.test_client()


def test_monthly_change_basic_flow(client):
    """Verify that /api/monthly_change returns months, totals and MoM changes."""
    res = client.get("/api/monthly_change")
    assert res.status_code == 200

    data = res.get_json()
    assert "changes" in data
    changes = data["changes"]

    # We inserted three months
    assert len(changes) == 3

    # January: first month, no change
    jan = changes[0]
    assert jan["month"] == "2025-01"
    assert jan["total"] == 10000.0
    assert jan["change"] is None
    assert jan["percent_change"] is None

    # February: +5000
    feb = changes[1]
    assert feb["month"] == "2025-02"
    assert feb["total"] == 15000.0
    assert feb["change"] == 5000.0
    assert round(feb["percent_change"], 2) == 50.0

    # March: -3000
    mar = changes[2]
    assert mar["month"] == "2025-03"
    assert mar["total"] == 12000.0
    assert mar["change"] == -3000.0
    assert round(mar["percent_change"], 2) == -20.0
