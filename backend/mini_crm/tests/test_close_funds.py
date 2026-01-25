"""
Tests for fund closing functionality.
"""

import pytest
import sqlite3
import datetime as dt
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from tools.mark_closed_funds import close_old_funds, get_fund_status_summary


@pytest.fixture
def tmp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_crm.db"
    
    # Create tables
    with sqlite3.connect(str(db_path)) as con:
        con.execute("""
            CREATE TABLE client (
                id INTEGER PRIMARY KEY,
                id_canon TEXT UNIQUE,
                name TEXT
            )
        """)
        
        con.execute("""
            CREATE TABLE snapshot (
                id INTEGER PRIMARY KEY,
                client_id INTEGER,
                fund_number TEXT,
                fund_type TEXT,
                fund_name TEXT,
                snapshot_date DATE,
                amount REAL,
                source TEXT,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (client_id) REFERENCES client(id)
            )
        """)
        
        # Create unique index
        con.execute("""
            CREATE UNIQUE INDEX snapshot_uq ON snapshot(client_id, fund_number, snapshot_date, source)
        """)
    
    # Temporarily override the DB path in the module
    import tools.mark_closed_funds
    original_db = tools.mark_closed_funds.DB
    tools.mark_closed_funds.DB = str(db_path)
    
    yield str(db_path)
    
    # Restore original DB path
    tools.mark_closed_funds.DB = original_db


def test_mark_closed_funds_basic(tmp_db):
    """Test basic fund closing functionality."""
    today = dt.date.today().replace(day=1)
    old_date = (today - dt.timedelta(days=90)).replace(day=1)  # 3 months ago
    recent_date = (today - dt.timedelta(days=30)).replace(day=1)  # 1 month ago
    
    with sqlite3.connect(tmp_db) as con:
        # Insert test client
        con.execute("INSERT INTO client (id_canon, name) VALUES ('123456789', 'Test Client')")
        client_id = con.lastrowid
        
        # Insert old fund (should be marked as closed)
        con.execute("""
            INSERT INTO snapshot (client_id, fund_number, fund_type, fund_name, 
                                snapshot_date, amount, source, is_active)
            VALUES (?, 'FUND001', 'קופת גמל', 'קופה ישנה', ?, 10000, 'TEST', 1)
        """, (client_id, old_date.isoformat()))
        
        # Insert recent fund (should remain active)
        con.execute("""
            INSERT INTO snapshot (client_id, fund_number, fund_type, fund_name, 
                                snapshot_date, amount, source, is_active)
            VALUES (?, 'FUND002', 'קופת גמל', 'קופה חדשה', ?, 20000, 'TEST', 1)
        """, (client_id, recent_date.isoformat()))
    
    # Run the closing function
    closed_count = close_old_funds(months=2)
    
    # Verify results
    assert closed_count == 1
    
    with sqlite3.connect(tmp_db) as con:
        # Check that old fund is marked as inactive
        old_fund_active = con.execute("""
            SELECT is_active FROM snapshot 
            WHERE fund_number = 'FUND001'
        """).fetchone()[0]
        assert old_fund_active == 0
        
        # Check that recent fund is still active
        recent_fund_active = con.execute("""
            SELECT is_active FROM snapshot 
            WHERE fund_number = 'FUND002'
        """).fetchone()[0]
        assert recent_fund_active == 1


def test_mark_closed_funds_no_funds_to_close(tmp_db):
    """Test when no funds need to be closed."""
    today = dt.date.today().replace(day=1)
    recent_date = (today - dt.timedelta(days=30)).replace(day=1)  # 1 month ago
    
    with sqlite3.connect(tmp_db) as con:
        # Insert test client
        con.execute("INSERT INTO client (id_canon, name) VALUES ('123456789', 'Test Client')")
        client_id = con.lastrowid
        
        # Insert recent fund (should remain active)
        con.execute("""
            INSERT INTO snapshot (client_id, fund_number, fund_type, fund_name, 
                                snapshot_date, amount, source, is_active)
            VALUES (?, 'FUND001', 'קופת גמל', 'קופה חדשה', ?, 10000, 'TEST', 1)
        """, (client_id, recent_date.isoformat()))
    
    # Run the closing function
    closed_count = close_old_funds(months=2)
    
    # Verify no funds were closed
    assert closed_count == 0
    
    with sqlite3.connect(tmp_db) as con:
        # Check that fund is still active
        fund_active = con.execute("""
            SELECT is_active FROM snapshot 
            WHERE fund_number = 'FUND001'
        """).fetchone()[0]
        assert fund_active == 1


def test_mark_closed_funds_multiple_sources(tmp_db):
    """Test fund closing with multiple sources."""
    today = dt.date.today().replace(day=1)
    old_date = (today - dt.timedelta(days=90)).replace(day=1)  # 3 months ago
    recent_date = (today - dt.timedelta(days=30)).replace(day=1)  # 1 month ago
    
    with sqlite3.connect(tmp_db) as con:
        # Insert test client
        con.execute("INSERT INTO client (id_canon, name) VALUES ('123456789', 'Test Client')")
        client_id = con.lastrowid
        
        # Insert same fund from different sources at different times
        con.execute("""
            INSERT INTO snapshot (client_id, fund_number, fund_type, fund_name, 
                                snapshot_date, amount, source, is_active)
            VALUES (?, 'FUND001', 'קופת גמל', 'קופה', ?, 10000, 'SOURCE1', 1)
        """, (client_id, old_date.isoformat()))
        
        con.execute("""
            INSERT INTO snapshot (client_id, fund_number, fund_type, fund_name, 
                                snapshot_date, amount, source, is_active)
            VALUES (?, 'FUND001', 'קופת גמל', 'קופה', ?, 15000, 'SOURCE2', 1)
        """, (client_id, recent_date.isoformat()))
    
    # Run the closing function
    closed_count = close_old_funds(months=2)
    
    # Verify that only the old source was closed
    assert closed_count == 1
    
    with sqlite3.connect(tmp_db) as con:
        # Check SOURCE1 (old) is inactive
        source1_active = con.execute("""
            SELECT is_active FROM snapshot 
            WHERE fund_number = 'FUND001' AND source = 'SOURCE1'
        """).fetchone()[0]
        assert source1_active == 0
        
        # Check SOURCE2 (recent) is still active
        source2_active = con.execute("""
            SELECT is_active FROM snapshot 
            WHERE fund_number = 'FUND001' AND source = 'SOURCE2'
        """).fetchone()[0]
        assert source2_active == 1


def test_get_fund_status_summary(tmp_db):
    """Test fund status summary function."""
    today = dt.date.today().replace(day=1)
    
    with sqlite3.connect(tmp_db) as con:
        # Insert test client
        con.execute("INSERT INTO client (id_canon, name) VALUES ('123456789', 'Test Client')")
        client_id = con.lastrowid
        
        # Insert active fund
        con.execute("""
            INSERT INTO snapshot (client_id, fund_number, fund_type, fund_name, 
                                snapshot_date, amount, source, is_active)
            VALUES (?, 'FUND001', 'קופת גמל', 'קופה פעילה', ?, 10000, 'TEST', 1)
        """, (client_id, today.isoformat()))
        
        # Insert inactive fund
        con.execute("""
            INSERT INTO snapshot (client_id, fund_number, fund_type, fund_name, 
                                snapshot_date, amount, source, is_active)
            VALUES (?, 'FUND002', 'קופת גמל', 'קופה לא פעילה', ?, 5000, 'TEST', 0)
        """, (client_id, today.isoformat()))
    
    # Get status summary
    active_count, inactive_count = get_fund_status_summary()
    
    # Verify counts
    assert active_count == 1
    assert inactive_count == 1


@pytest.mark.parametrize("months", [2, 3])
def test_close_logic(tmp_db, months):
    """
    1. צור שלושה snapshots לחודש נוכחי-2, נוכחי-1, נוכחי.
    2. הרץ mark_closed_funds.py --months=<months>
    3. ודא שקופה א׳ מחודש -2 הפכה is_active=0
       ושאר הקופות נשארו is_active=1.
    """
    today = dt.date.today().replace(day=1)
    month_minus_2 = (today - dt.timedelta(days=62)).replace(day=1)  # 2+ months ago
    month_minus_1 = (today - dt.timedelta(days=31)).replace(day=1)  # 1 month ago
    current_month = today
    
    with sqlite3.connect(tmp_db) as con:
        # Insert test client
        con.execute("INSERT INTO client (id_canon, name) VALUES ('123456789', 'Test Client')")
        client_id = con.lastrowid
        
        # Insert fund from 2+ months ago (should be closed if months <= 2)
        con.execute("""
            INSERT INTO snapshot (client_id, fund_number, fund_type, fund_name, 
                                snapshot_date, amount, source, is_active)
            VALUES (?, 'FUND001', 'קופת גמל', 'קופה ישנה', ?, 10000, 'TEST', 1)
        """, (client_id, month_minus_2.isoformat()))
        
        # Insert fund from 1 month ago (should remain active)
        con.execute("""
            INSERT INTO snapshot (client_id, fund_number, fund_type, fund_name, 
                                snapshot_date, amount, source, is_active)
            VALUES (?, 'FUND002', 'קופת גמל', 'קופה חדשה', ?, 15000, 'TEST', 1)
        """, (client_id, month_minus_1.isoformat()))
        
        # Insert fund from current month (should remain active)
        con.execute("""
            INSERT INTO snapshot (client_id, fund_number, fund_type, fund_name, 
                                snapshot_date, amount, source, is_active)
            VALUES (?, 'FUND003', 'קופת גמל', 'קופה עדכנית', ?, 20000, 'TEST', 1)
        """, (client_id, current_month.isoformat()))
    
    # Run the closing function
    closed_count = close_old_funds(months=months)
    
    with sqlite3.connect(tmp_db) as con:
        # Check FUND001 (2+ months old)
        fund001_active = con.execute("""
            SELECT is_active FROM snapshot WHERE fund_number = 'FUND001'
        """).fetchone()[0]
        
        # Check FUND002 (1 month old)
        fund002_active = con.execute("""
            SELECT is_active FROM snapshot WHERE fund_number = 'FUND002'
        """).fetchone()[0]
        
        # Check FUND003 (current month)
        fund003_active = con.execute("""
            SELECT is_active FROM snapshot WHERE fund_number = 'FUND003'
        """).fetchone()[0]
        
        if months <= 2:
            # FUND001 should be closed, others should remain active
            assert fund001_active == 0, f"FUND001 should be closed with {months} months threshold"
            assert closed_count == 1
        else:
            # All funds should remain active
            assert fund001_active == 1, f"FUND001 should remain active with {months} months threshold"
            assert closed_count == 0
            
        # FUND002 and FUND003 should always remain active
        assert fund002_active == 1, "FUND002 should always remain active"
        assert fund003_active == 1, "FUND003 should always remain active"


def test_mark_closed_funds_custom_months(tmp_db):
    """Test fund closing with custom months parameter."""
    today = dt.date.today().replace(day=1)
    old_date = (today - dt.timedelta(days=150)).replace(day=1)  # 5 months ago
    
    with sqlite3.connect(tmp_db) as con:
        # Insert test client
        con.execute("INSERT INTO client (id_canon, name) VALUES ('123456789', 'Test Client')")
        client_id = con.lastrowid
        
        # Insert old fund
        con.execute("""
            INSERT INTO snapshot (client_id, fund_number, fund_type, fund_name, 
                                snapshot_date, amount, source, is_active)
            VALUES (?, 'FUND001', 'קופת גמל', 'קופה ישנה', ?, 10000, 'TEST', 1)
        """, (client_id, old_date.isoformat()))
    
    # Run with 3 months threshold (should close the fund)
    closed_count = close_old_funds(months=3)
    assert closed_count == 1
    
    # Reset the fund to active
    with sqlite3.connect(tmp_db) as con:
        con.execute("UPDATE snapshot SET is_active = 1 WHERE fund_number = 'FUND001'")
    
    # Run with 6 months threshold (should not close the fund)
    closed_count = close_old_funds(months=6)
    assert closed_count == 0
