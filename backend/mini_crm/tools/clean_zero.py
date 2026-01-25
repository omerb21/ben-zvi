"""
Clean zero-balance snapshots from the database.
This script removes all snapshots with amount = 0 from the database.
"""
import sqlite3
import sys
import os
from pathlib import Path

# Add parent directory to path to import DB constant
sys.path.insert(0, str(Path(__file__).parent.parent))

def clean_zero_balances():
    """Remove all zero-balance snapshots from the database."""
    
    # Use the same DB path as the main app
    db_path = os.environ.get('CRM_DB', 'crm.db')
    
    try:
        with sqlite3.connect(db_path) as con:
            # Count zero-balance snapshots before deletion
            count_before = con.execute("SELECT COUNT(*) FROM snapshot WHERE amount = 0").fetchone()[0]
            
            if count_before == 0:
                print("🎉 No zero-balance snapshots found. Database is clean!")
                return
            
            print(f"Found {count_before} zero-balance snapshots.")
            
            # Ask for confirmation
            response = input("Do you want to delete these records? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("❌ Operation cancelled.")
                return
            
            # Delete zero-balance snapshots
            deleted = con.execute("DELETE FROM snapshot WHERE amount = 0").rowcount
            con.commit()
            
            print(f"🧹 Removed {deleted} zero-balance snapshots")
            
            # Verify deletion
            count_after = con.execute("SELECT COUNT(*) FROM snapshot WHERE amount = 0").fetchone()[0]
            if count_after == 0:
                print("✅ All zero-balance snapshots successfully removed!")
            else:
                print(f"⚠️  Warning: {count_after} zero-balance snapshots still remain")
                
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🧹 Zero-Balance Snapshot Cleanup Tool")
    print("=====================================")
    clean_zero_balances()
