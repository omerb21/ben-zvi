"""
Tests for client report functionality.
"""
import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, date
import pandas as pd
from reports.client_report import fetch_client_funds, _client_data, bp_reports
from flask import Flask


@pytest.fixture
def app():
    """Create test Flask app."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(bp_reports)
    return app


@pytest.fixture
def app_client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def tmp_db():
    """Create temporary database with test data."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    # Create tables and insert test data
    with sqlite3.connect(db_path) as con:
        # Create client table
        con.execute("""
            CREATE TABLE client (
                id INTEGER PRIMARY KEY,
                id_canon TEXT UNIQUE,
                name TEXT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                email TEXT
            )
        """)
        
        # Create snapshot table
        con.execute("""
            CREATE TABLE snapshot (
                id INTEGER PRIMARY KEY,
                client_id INTEGER,
                fund_code TEXT,
                fund_number TEXT,
                fund_type TEXT,
                fund_name TEXT,
                snapshot_date TEXT,
                amount REAL,
                source TEXT,
                company TEXT,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY(client_id) REFERENCES client(id)
            )
        """)
        
        # Insert test client
        con.execute("""
            INSERT INTO client (id_canon, name, first_name, last_name, phone, email)
            VALUES ('123456789', 'יוסי כהן', 'יוסי', 'כהן', '050-1234567', 'yossi@example.com')
        """)
        client_id = con.lastrowid
        
        # Insert test snapshots
        test_snapshots = [
            (client_id, 'FUND001', 'קופת גמל', 'קופה ראשונה', '2025-07-01', 50000, 'FNX', 'פניקס', 1),
            (client_id, 'FUND002', 'קרן השתלמות', 'קופה שנייה', '2025-07-01', 30000, 'MOR', 'מור', 1),
            (client_id, 'FUND003', 'גמל להשקעה', 'קופה שלישית', '2025-06-01', 20000, 'YL', 'יהב לוי', 1),
            (client_id, 'FUND004', 'קופת גמל', 'קופה סגורה', '2025-05-01', 15000, 'HAR', 'הראל', 0),  # inactive
        ]
        
        for snapshot in test_snapshots:
            con.execute("""
                INSERT INTO snapshot (client_id, fund_number, fund_type, fund_name, 
                                    snapshot_date, amount, source, company, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, snapshot)
    
    # Temporarily replace the database path
    original_db = 'crm.db'
    import reports.client_report
    reports.client_report.sqlite3.connect = lambda path: sqlite3.connect(db_path)
    
    yield client_id
    
    # Cleanup
    os.unlink(db_path)


def test_fetch_client_funds_latest(tmp_db):
    """Test fetching client funds without month filter (latest)."""
    client_id = tmp_db
    df = fetch_client_funds(client_id)
    
    # Should return only active funds from latest date (2025-07-01)
    assert len(df) == 2  # FUND001 and FUND002
    assert df['snapshot_date'].iloc[0] == '2025-07-01'
    assert df['amount'].sum() == 80000  # 50000 + 30000


def test_fetch_client_funds_specific_month(tmp_db):
    """Test fetching client funds for specific month."""
    client_id = tmp_db
    df = fetch_client_funds(client_id, '2025-06')
    
    # Should return only active funds from June 2025
    assert len(df) == 1  # Only FUND003
    assert df['fund_number'].iloc[0] == 'FUND003'
    assert df['amount'].iloc[0] == 20000


def test_fetch_client_funds_no_data(tmp_db):
    """Test fetching client funds when no data exists."""
    client_id = tmp_db
    df = fetch_client_funds(client_id, '2025-01')  # No data for this month
    
    assert df.empty


def test_client_data(tmp_db):
    """Test fetching client basic data."""
    client_id = tmp_db
    client = _client_data(client_id)
    
    assert client['id_canon'] == '123456789'
    assert client['name'] == 'יוסי כהן'
    assert client['first_name'] == 'יוסי'
    assert client['last_name'] == 'כהן'
    assert client['phone'] == '050-1234567'
    assert client['email'] == 'yossi@example.com'


@pytest.mark.parametrize('fmt', ['csv', 'xlsx'])  # Skip PDF for now due to dependencies
def test_report_status(app_client, tmp_db, fmt):
    """Test report generation status codes."""
    client_id = tmp_db
    url = f'/report/client/{client_id}.{fmt}?month=2025-07'
    
    response = app_client.get(url)
    assert response.status_code == 200
    assert 'attachment' in response.headers.get('Content-Disposition', '')


def test_report_csv_content(app_client, tmp_db):
    """Test CSV report content."""
    client_id = tmp_db
    url = f'/report/client/{client_id}.csv?month=2025-07'
    
    response = app_client.get(url)
    assert response.status_code == 200
    
    content = response.data.decode('utf-8-sig')
    assert 'מס\' קופה' in content  # Hebrew column header
    assert 'FUND001' in content
    assert 'FUND002' in content
    assert 'פניקס' in content
    assert 'מור' in content


def test_report_xlsx_content(app_client, tmp_db):
    """Test Excel report content."""
    client_id = tmp_db
    url = f'/report/client/{client_id}.xlsx?month=2025-07'
    
    response = app_client.get(url)
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


def test_report_invalid_month(app_client, tmp_db):
    """Test report with invalid month format."""
    client_id = tmp_db
    url = f'/report/client/{client_id}.csv?month=invalid-month'
    
    response = app_client.get(url)
    assert response.status_code == 400


def test_report_unsupported_format(app_client, tmp_db):
    """Test report with unsupported format."""
    client_id = tmp_db
    url = f'/report/client/{client_id}.txt'
    
    response = app_client.get(url)
    assert response.status_code == 400


def test_report_nonexistent_client(app_client):
    """Test report for non-existent client."""
    url = '/report/client/99999.csv'
    
    response = app_client.get(url)
    assert response.status_code == 404


def test_report_no_data_for_month(app_client, tmp_db):
    """Test report when no data exists for specified month."""
    client_id = tmp_db
    url = f'/report/client/{client_id}.csv?month=2025-01'
    
    response = app_client.get(url)
    assert response.status_code == 404


def test_report_latest_month(app_client, tmp_db):
    """Test report without month parameter (should get latest)."""
    client_id = tmp_db
    url = f'/report/client/{client_id}.csv'
    
    response = app_client.get(url)
    assert response.status_code == 200
    
    content = response.data.decode('utf-8-sig')
    # Should contain data from latest month (July 2025)
    assert 'FUND001' in content
    assert 'FUND002' in content
    # Should not contain June data
    assert 'FUND003' not in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
