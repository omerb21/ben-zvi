"""
Test dashboard API endpoints.
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
        
        # Insert some test data
        test_data = pd.DataFrame({
            'client_name': ['בדיקה יוסף', 'בדיקה יוסף', 'שרה כהן'],
            'id_canon': ['123456789', '123456789', '987654321'],
            'fund_number': ['TEST-001', 'TEST-002', 'TEST-003'],
            'fund_code': ['TST001', 'TST002', 'TST003'],
            'fund_type': ['מניות', 'אגח', 'מניות'],
            'fund_name': ['קרן בדיקה 1', 'קרן בדיקה 2', 'קרן בדיקה 3'],
            'accumulated_amount': [10000.0, 5000.0, 7500.0],
            'client_key': ['בדיקה יוסף_123456789', 'בדיקה יוסף_123456789', 'שרה כהן_987654321']
        })
        
        insert_rows(test_data, source="TEST", snap_date="2025-07-01")

        # Ensure key HTML routes are available on this test app instance
        # by reusing the real view functions from the app module.
        app.add_url_rule("/", view_func=app_module.index)
        app.add_url_rule("/clients/", view_func=app_module.clients)
        app.add_url_rule("/upload/", view_func=app_module.upload)
        app.add_url_rule("/dashboard/", view_func=app_module.dashboard)
        
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

def test_api_summary(client):
    """Test the /api/summary endpoint."""
    res = client.get("/api/summary")
    assert res.status_code == 200
    
    json_data = res.get_json()
    assert {"total_assets", "by_source", "by_fund_type"} <= json_data.keys()
    
    # Check that we have the expected total
    assert json_data["total_assets"] == 22500.0
    
    # Check that we have data by source
    assert "TEST" in json_data["by_source"]
    assert json_data["by_source"]["TEST"] == 22500.0
    
    # Check that we have data by fund type
    assert "מניות" in json_data["by_fund_type"]
    assert "אגח" in json_data["by_fund_type"]


def test_api_summary_with_month_filter(client):
    """Test that /api/summary respects the month query parameter."""
    # Month with data (July 2025)
    res_july = client.get("/api/summary?month=2025-07")
    assert res_july.status_code == 200
    data_july = res_july.get_json()
    assert data_july["total_assets"] == 22500.0

    # Month without data should return 0 totals
    res_dec = client.get("/api/summary?month=2025-12")
    assert res_dec.status_code == 200
    data_dec = res_dec.get_json()
    assert data_dec["total_assets"] == 0

def test_api_history_all_clients(client):
    """Test the /api/history endpoint with client_id=0 (all clients)."""
    res = client.get("/api/history?client_id=0")
    assert res.status_code == 200
    
    json_data = res.get_json()
    assert "history" in json_data
    assert len(json_data["history"]) > 0
    
    # Check the structure of history data
    history_item = json_data["history"][0]
    assert "month" in history_item
    assert "amount" in history_item
    assert history_item["month"] == "2025-07"
    assert history_item["amount"] == 22500.0

def test_api_history_specific_client(client, app):
    """Test the /api/history endpoint with a specific client_id."""
    # First, get the client_id for our test client from the test database
    db_path = app.config["DB"]
    with sqlite3.connect(db_path) as con:
        client_id = con.execute("SELECT id FROM client WHERE id_canon = ?", ("123456789",)).fetchone()[0]
    
    res = client.get(f"/api/history?client_id={client_id}")
    assert res.status_code == 200
    
    json_data = res.get_json()
    assert "history" in json_data
    assert len(json_data["history"]) > 0
    
    # Check that the amount is correct for this specific client
    history_item = json_data["history"][0]
    assert history_item["amount"] == 15000.0  # 10000 + 5000

def test_api_history_missing_client_id(client):
    """Test the /api/history endpoint without client_id parameter."""
    res = client.get("/api/history")
    assert res.status_code == 400
    
    json_data = res.get_json()
    assert "error" in json_data
    assert "client_id required" in json_data["error"]

def test_dashboard_page(client):
    """Test that the dashboard page loads correctly."""
    res = client.get("/dashboard/")
    assert res.status_code == 200
    assert "דשבורד תיק לקוחות" in res.get_data(as_text=True)
