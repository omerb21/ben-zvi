"""
Test reports endpoints.
"""
import pytest
import tempfile
import os
import sqlite3
import pandas as pd
from pathlib import Path
import sys
import csv
import io

# Add the parent directory to the path so we can import from the project
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, init_db, insert_rows

@pytest.fixture
def app():
    """Create and configure a test app."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['DB'] = db_path
    
    with app.app_context():
        # Override the DB constant temporarily
        import app as app_module
        original_db = app_module.DB
        app_module.DB = db_path
        
        # Initialize the test database
        init_db()
        
        # Insert test data for July 2025
        test_data_july = pd.DataFrame({
            'client_name': ['בדיקה יוסף', 'שרה כהן'],
            'id_canon': ['123456789', '987654321'],
            'fund_number': ['TEST-001', 'TEST-002'],
            'fund_code': ['TST001', 'TST002'],
            'fund_type': ['מניות', 'אגח'],
            'fund_name': ['קרן בדיקה 1', 'קרן בדיקה 2'],
            'accumulated_amount': [10000.0, 5000.0],
            'client_key': ['בדיקה יוסף_123456789', 'שרה כהן_987654321']
        })
        
        # Insert test data for August 2025
        test_data_august = pd.DataFrame({
            'client_name': ['בדיקה יוסף', 'שרה כהן'],
            'id_canon': ['123456789', '987654321'],
            'fund_number': ['TEST-001', 'TEST-002'],
            'fund_code': ['TST001', 'TST002'],
            'fund_type': ['מניות', 'אגח'],
            'fund_name': ['קרן בדיקה 1', 'קרן בדיקה 2'],
            'accumulated_amount': [12000.0, 6000.0],
            'client_key': ['בדיקה יוסף_123456789', 'שרה כהן_987654321']
        })
        
        insert_rows(test_data_july, source="TEST", snap_date="2025-07-15")
        insert_rows(test_data_august, source="TEST", snap_date="2025-08-15")
        
        # Restore original DB
        app_module.DB = original_db
    
    yield app
    
    # Clean up
    try:
        os.unlink(db_path)
    except:
        pass

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

def test_report_csv_valid_month(client):
    """Test CSV export for a valid month."""
    res = client.get("/report/funds?month=2025-07")
    assert res.status_code == 200
    assert res.mimetype == "text/csv"
    assert "attachment" in res.headers["Content-Disposition"]
    assert "funds_2025-07.csv" in res.headers["Content-Disposition"]
    
    # Parse the CSV content
    csv_content = res.get_data(as_text=True)
    csv_reader = csv.reader(io.StringIO(csv_content))
    
    # Check header
    header = next(csv_reader)
    expected_header = ["client_name", "id_canon", "fund_number", "fund_name", "fund_type", "amount", "source"]
    assert header == expected_header
    
    # Check data rows
    rows = list(csv_reader)
    assert len(rows) == 2  # We inserted 2 records for July
    
    # Check first row (should be sorted by client name)
    first_row = rows[0]
    assert first_row[0] == "בדיקה יוסף"  # client_name
    assert first_row[1] == "123456789"   # id_canon
    assert first_row[2] == "TEST-001"    # fund_number
    assert float(first_row[5]) == 10000.0  # amount

def test_report_csv_different_month(client):
    """Test CSV export for a different month."""
    res = client.get("/report/funds?month=2025-08")
    assert res.status_code == 200
    assert res.mimetype == "text/csv"
    
    # Parse the CSV content
    csv_content = res.get_data(as_text=True)
    csv_reader = csv.reader(io.StringIO(csv_content))
    
    # Skip header
    next(csv_reader)
    
    # Check data rows
    rows = list(csv_reader)
    assert len(rows) == 2  # We inserted 2 records for August
    
    # Check that amounts are different (updated values)
    amounts = [float(row[5]) for row in rows]
    assert 12000.0 in amounts
    assert 6000.0 in amounts

def test_report_csv_missing_month(client):
    """Test CSV export without month parameter."""
    res = client.get("/report/funds")
    assert res.status_code == 400
    
    json_data = res.get_json()
    assert "error" in json_data
    assert "month parameter required" in json_data["error"]

def test_report_csv_invalid_month_format(client):
    """Test CSV export with invalid month format."""
    res = client.get("/report/funds?month=invalid-format")
    assert res.status_code == 400
    
    json_data = res.get_json()
    assert "error" in json_data
    assert "month parameter format YYYY-MM" in json_data["error"]

def test_report_csv_nonexistent_month(client):
    """Test CSV export for a month with no data."""
    res = client.get("/report/funds?month=2025-12")
    assert res.status_code == 200
    assert res.mimetype == "text/csv"
    
    # Parse the CSV content
    csv_content = res.get_data(as_text=True)
    csv_reader = csv.reader(io.StringIO(csv_content))
    
    # Check header exists
    header = next(csv_reader)
    assert len(header) == 7
    
    # Check no data rows
    rows = list(csv_reader)
    assert len(rows) == 0


def test_monthly_change_csv(client):
    """Test monthly change CSV export."""
    res = client.get("/report/monthly_change")
    assert res.status_code == 200
    assert res.mimetype == "text/csv"
    assert "attachment" in res.headers["Content-Disposition"]
    assert "monthly_change.csv" in res.headers["Content-Disposition"]

    csv_content = res.get_data(as_text=True)
    csv_reader = csv.reader(io.StringIO(csv_content))

    # Header
    header = next(csv_reader)
    assert header == ["month", "total", "change", "percent_change"]

    rows = list(csv_reader)
    # We inserted data for two months (July and August)
    assert len(rows) == 2

    # First month should be July (2025-07) with total 15000 and no change
    first = rows[0]
    assert first[0] == "2025-07"
    assert float(first[1]) == 15000.0
    assert first[2] == ""  # change
    assert first[3] == ""  # percent_change

    # Second month should be August (2025-08) with higher total and positive change
    second = rows[1]
    assert second[0] == "2025-08"
    assert float(second[1]) == 18000.0
    # Absolute change 3000
    assert float(second[2]) == 3000.0
    # Percent change 20% formatted to two decimals
    assert float(second[3]) == 20.00


def test_client_report_csv(client, app):
    """Test client report CSV export for a specific client."""
    db_path = app.config["DB"]
    with sqlite3.connect(db_path) as con:
        row = con.execute(
            "SELECT id FROM client WHERE id_canon = ?",
            ("123456789",),
        ).fetchone()

    assert row is not None
    client_id = row[0]

    res = client.get(f"/report/client/{client_id}?month=2025-07")
    assert res.status_code == 200
    assert res.mimetype == "text/csv"

    csv_content = res.get_data(as_text=True)
    csv_reader = csv.reader(io.StringIO(csv_content))

    header = next(csv_reader)
    assert len(header) == 10

    rows = list(csv_reader)
    # We expect exactly one row for this client for the given month
    assert len(rows) == 1
    first_row = rows[0]
    # Ensure the ID appears in the row
    assert "123456789" in first_row
