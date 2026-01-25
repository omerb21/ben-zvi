"""
Test monthly snapshot history functionality.
"""
import sqlite3
import tempfile
import os
from datetime import date, datetime
import pytest
import pandas as pd
from pathlib import Path

# Add the parent directory to the path so we can import from the project
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import init_db, insert_rows

def setup_test_db():
    """Setup a clean test database."""
    import tempfile
    import os
    
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    # Temporarily override the DB constant
    import app
    original_db = app.DB
    app.DB = db_path
    
    # Initialize the test database
    init_db()
    
    return db_path, original_db

def cleanup_test_db(db_path, original_db):
    """Clean up test database and restore original DB."""
    import app
    import os
    
    app.DB = original_db
    try:
        os.unlink(db_path)
    except:
        pass

def test_monthly_history():
    """Test that monthly snapshots are stored separately and can be updated."""
    
    db_path, original_db = setup_test_db()
    
    try:
        # Create test data
        test_data = pd.DataFrame({
            'client_name': ['עומר בן צבי', 'עומר בן צבי'],
            'id_canon': ['034458497', '034458497'],
            'fund_number': ['277654', '277655'],
            'fund_code': ['FNX001', 'FNX002'],
            'fund_type': ['מניות', 'אגח'],
            'fund_name': ['קרן מניות', 'קרן אגח'],
            'accumulated_amount': [10000.0, 5000.0],
            'client_key': ['עומר בן צבי_034458497', 'עומר בן צבי_034458497']
        })
        
        # 1. Load data for June 2025 (2025-06-15)
        insert_rows(test_data, source="FNX", snap_date="2025-06-15")
        
        # 2. Load same data for July 2025 (2025-07-15) 
        test_data_july = test_data.copy()
        test_data_july['accumulated_amount'] = [12000.0, 6000.0]  # Different amounts
        insert_rows(test_data_july, source="FNX", snap_date="2025-07-15")
        
        # 3. Verify we have 2 snapshots for each fund (one per month)
        import app
        with sqlite3.connect(app.DB) as con:
            # Check total snapshots
            total_count = con.execute("SELECT COUNT(*) FROM snapshot").fetchone()[0]
            assert total_count == 4, f"Expected 4 snapshots, got {total_count}"
            
            # Check snapshots for fund 277654
            fund_snapshots = con.execute("""
                SELECT snapshot_date, amount FROM snapshot 
                WHERE fund_number=? 
                ORDER BY snapshot_date
            """, ("277654",)).fetchall()
            
            assert len(fund_snapshots) == 2, f"Expected 2 snapshots for fund 277654, got {len(fund_snapshots)}"
            
            # Verify dates are normalized to first of month
            june_snapshot = fund_snapshots[0]
            july_snapshot = fund_snapshots[1]
            
            assert june_snapshot[0] == "2025-06-01", f"June date should be 2025-06-01, got {june_snapshot[0]}"
            assert july_snapshot[0] == "2025-07-01", f"July date should be 2025-07-01, got {july_snapshot[0]}"
            
            # Verify amounts
            assert june_snapshot[1] == 10000.0, f"June amount should be 10000.0, got {june_snapshot[1]}"
            assert july_snapshot[1] == 12000.0, f"July amount should be 12000.0, got {july_snapshot[1]}"
    
    finally:
        cleanup_test_db(db_path, original_db)

def test_monthly_update_same_month():
    """Test that loading data twice for the same month updates (replaces) the data."""
    
    db_path, original_db = setup_test_db()
    
    try:
        # Create test data
        test_data = pd.DataFrame({
            'client_name': ['דני כהן'],
            'id_canon': ['123456789'],
            'fund_number': ['888999'],
            'fund_code': ['TEST001'],
            'fund_type': ['מניות'],
            'fund_name': ['קרן בדיקה'],
            'accumulated_amount': [5000.0],
            'client_key': ['דני כהן_123456789']
        })
        
        # 1. Load data for June 2025 (2025-06-10)
        insert_rows(test_data, source="TEST", snap_date="2025-06-10")
        
        # 2. Load updated data for same month (2025-06-25) - should replace
        test_data_updated = test_data.copy()
        test_data_updated['accumulated_amount'] = [7500.0]  # Updated amount
        insert_rows(test_data_updated, source="TEST", snap_date="2025-06-25")
        
        # 3. Verify we have only 1 snapshot (replaced, not duplicated)
        import app
        with sqlite3.connect(app.DB) as con:
            snapshots = con.execute("""
                SELECT snapshot_date, amount FROM snapshot 
                WHERE fund_number=? AND source=?
            """, ("888999", "TEST")).fetchall()
            
            assert len(snapshots) == 1, f"Expected 1 snapshot (replaced), got {len(snapshots)}"
            
            # Verify the amount was updated
            snapshot = snapshots[0]
            assert snapshot[0] == "2025-06-01", f"Date should be 2025-06-01, got {snapshot[0]}"
            assert snapshot[1] == 7500.0, f"Amount should be updated to 7500.0, got {snapshot[1]}"
    
    finally:
        cleanup_test_db(db_path, original_db)

def test_date_normalization():
    """Test that various dates within a month are normalized to the first day."""
    
    db_path, original_db = setup_test_db()
    
    try:
        test_data = pd.DataFrame({
            'client_name': ['רחל לוי'],
            'id_canon': ['987654321'],
            'fund_number': ['111222'],
            'fund_code': ['NORM001'],
            'fund_type': ['מניות'],
            'fund_name': ['קרן נורמליזציה'],
            'accumulated_amount': [3000.0],
            'client_key': ['רחל לוי_987654321']
        })
        
        # Test different dates in March 2025
        test_dates = ["2025-03-01", "2025-03-15", "2025-03-31"]
        
        for i, test_date in enumerate(test_dates):
            # Update amount for each iteration to see the replacement
            test_data_copy = test_data.copy()
            test_data_copy['accumulated_amount'] = [3000.0 + (i * 1000)]
            insert_rows(test_data_copy, source="NORM", snap_date=test_date)
        
        # Verify only one snapshot exists with the last amount
        import app
        with sqlite3.connect(app.DB) as con:
            snapshots = con.execute("""
                SELECT snapshot_date, amount FROM snapshot 
                WHERE fund_number=? AND source=?
            """, ("111222", "NORM")).fetchall()
            
            assert len(snapshots) == 1, f"Expected 1 snapshot (all dates normalized), got {len(snapshots)}"
            
            snapshot = snapshots[0]
            assert snapshot[0] == "2025-03-01", f"Date should be normalized to 2025-03-01, got {snapshot[0]}"
            assert snapshot[1] == 5000.0, f"Amount should be final value 5000.0, got {snapshot[1]}"
    
    finally:
        cleanup_test_db(db_path, original_db)

if __name__ == "__main__":
    # Run tests
    print("Running monthly history tests...")
    
    try:
        test_monthly_history()
        print("✅ test_monthly_history passed")
        
        test_monthly_update_same_month()
        print("✅ test_monthly_update_same_month passed")
        
        test_date_normalization()
        print("✅ test_date_normalization passed")
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
