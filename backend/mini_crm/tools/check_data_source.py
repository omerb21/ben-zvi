"""
Check data sources to determine which one the dashboard is reading from.
"""
import sqlite3
import os
import sys

def main():
    """Run diagnostic queries and print results."""
    db_path = os.environ.get("CRM_DB", "crm.db")
    if not os.path.exists(db_path):
        print(f"Error: Database file {db_path} not found")
        sys.exit(1)
    
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if tables exist
    print("\nChecking tables...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables found: {', '.join(tables)}")
    
    # Check if client_positions_monthly exists
    if 'client_positions_monthly' in tables:
        print("\nChecking client_positions_monthly structure...")
        cursor.execute("PRAGMA table_info(client_positions_monthly)")
        columns = [row['name'] for row in cursor.fetchall()]
        print(f"Columns: {', '.join(columns)}")
        
        # Check total in client_positions_monthly
        balance_column = 'balance_amount' if 'balance_amount' in columns else 'amount'
        cursor.execute(f"SELECT COALESCE(SUM({balance_column}), 0) AS total FROM client_positions_monthly")
        total = cursor.fetchone()[0]
        print(f"\nTotal in client_positions_monthly: {total}")
        
        # Check if view exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='vw_client_positions_latest'")
        if cursor.fetchone():
            try:
                cursor.execute("SELECT COALESCE(SUM(balance_amount), 0) AS total_latest FROM vw_client_positions_latest")
                total_latest = cursor.fetchone()[0]
                print(f"Total in vw_client_positions_latest: {total_latest}")
            except sqlite3.OperationalError as e:
                print(f"Error querying vw_client_positions_latest: {e}")
                # Try to get the view definition
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='view' AND name='vw_client_positions_latest'")
                view_def = cursor.fetchone()
                if view_def:
                    print(f"View definition: {view_def[0]}")
        else:
            print("View vw_client_positions_latest does not exist")
    
    # Check snapshot table
    print("\nChecking snapshot structure...")
    cursor.execute("PRAGMA table_info(snapshot)")
    columns = [row['name'] for row in cursor.fetchall()]
    print(f"Columns: {', '.join(columns)}")
    
    # Check total in snapshot
    balance_column = 'balance_amount' if 'balance_amount' in columns else 'amount'
    cursor.execute(f"SELECT COALESCE(SUM({balance_column}), 0) AS total_snapshot FROM snapshot")
    total_snapshot = cursor.fetchone()[0]
    print(f"\nTotal in snapshot: {total_snapshot}")
    
    # Check if client_positions_monthly has client_id as text
    if 'client_positions_monthly' in tables:
        cursor.execute("SELECT typeof(client_id) FROM client_positions_monthly LIMIT 1")
        result = cursor.fetchone()
        if result:
            client_id_type = result[0]
            print(f"\nClient ID type in client_positions_monthly: {client_id_type}")
            
            # Check if there are any records with text client_id
            cursor.execute("SELECT COUNT(*) FROM client_positions_monthly WHERE typeof(client_id) <> 'integer'")
            text_client_ids = cursor.fetchone()[0]
            print(f"Records with non-integer client_id: {text_client_ids}")
    
    conn.close()

if __name__ == "__main__":
    main()
