#!/usr/bin/env python3
"""
Cleanup script to remove zero-balance snapshots from the database.

This script removes all snapshot records where:
- accumulated_amount <= 0 
- accumulated_amount IS NULL

Usage:
    python tools/cleanup_zero_balances.py
"""

import sqlite3
import sys
import os
import textwrap
from pathlib import Path

# Get database path
DB = os.getenv("CRM_DB", "crm.db")

def main():
    """Remove zero-balance snapshots from the database."""
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    db_path = project_root / DB
    
    if not db_path.exists():
        print(f"❌ Database file not found: {db_path}")
        print("Make sure you're running this from the project root or set CRM_DB environment variable.")
        sys.exit(1)
    
    print(f"🔍 Checking database: {db_path}")
    
    with sqlite3.connect(str(db_path)) as con:
        # Count zero-balance snapshots
        to_delete = con.execute(
            "SELECT COUNT(*) FROM snapshot WHERE amount <= 0 OR amount IS NULL"
        ).fetchone()[0]
        
        if not to_delete:
            print("✅ No zero-balance snapshots found.")
            print("Database is clean!")
            return
        
        # Show current stats
        total_snapshots = con.execute("SELECT COUNT(*) FROM snapshot").fetchone()[0]
        print(f"📊 Current database stats:")
        print(f"   Total snapshots: {total_snapshots}")
        print(f"   Zero-balance snapshots: {to_delete}")
        print(f"   Valid snapshots: {total_snapshots - to_delete}")
        
        # Confirm deletion
        print(f"\n⚠️  About to delete {to_delete} zero-balance snapshots.")
        response = input("Continue? (y/N): ").strip().lower()
        
        if response not in ['y', 'yes']:
            print("❌ Operation cancelled.")
            return
        
        # Delete zero-balance snapshots
        print("🧹 Removing zero-balance snapshots...")
        con.execute(
            "DELETE FROM snapshot WHERE amount <= 0 OR amount IS NULL"
        )
        con.commit()
        
        # Show final stats
        remaining_snapshots = con.execute("SELECT COUNT(*) FROM snapshot").fetchone()[0]
        
        print(textwrap.dedent(f"""
        ✅ Cleanup completed successfully!
        
        📊 Results:
           Removed snapshots: {to_delete}
           Remaining snapshots: {remaining_snapshots}
           
        💡 Database is now clean of zero-balance records.
        """).strip())

if __name__ == "__main__":
    main()
