import sqlite3
import os

db_path = os.environ.get("CRM_DB", "crm.db")
if not os.path.exists(db_path):
    print(f"Error: Database file {db_path} not found")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# List all tables
print("Tables in database:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
for table in tables:
    print(f"- {table[0]}")

# Check if client_positions_monthly exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='client_positions_monthly'")
if cursor.fetchone():
    print("\nTable client_positions_monthly exists")
    
    # Get column names
    cursor.execute("PRAGMA table_info(client_positions_monthly)")
    columns = cursor.fetchall()
    print("Columns in client_positions_monthly:")
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
    
    # Check if balance_amount column exists
    balance_col = "balance_amount"
    cursor.execute(f"PRAGMA table_info(client_positions_monthly)")
    columns = [col[1] for col in cursor.fetchall()]
    if balance_col in columns:
        cursor.execute(f"SELECT COALESCE(SUM({balance_col}), 0) FROM client_positions_monthly")
        total = cursor.fetchone()[0]
        print(f"\nTotal in client_positions_monthly ({balance_col}): {total}")
    else:
        print(f"\nColumn {balance_col} not found in client_positions_monthly")
        # Try with 'amount' instead
        if 'amount' in columns:
            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM client_positions_monthly")
            total = cursor.fetchone()[0]
            print(f"Total in client_positions_monthly (amount): {total}")
else:
    print("\nTable client_positions_monthly does not exist")

# Check snapshot table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='snapshot'")
if cursor.fetchone():
    print("\nTable snapshot exists")
    
    # Get column names
    cursor.execute("PRAGMA table_info(snapshot)")
    columns = cursor.fetchall()
    print("Columns in snapshot:")
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
    
    # Check total in snapshot
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM snapshot")
    total_snapshot = cursor.fetchone()[0]
    print(f"\nTotal in snapshot (amount): {total_snapshot}")
else:
    print("\nTable snapshot does not exist")

# Check if view exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='vw_client_positions_latest'")
if cursor.fetchone():
    print("\nView vw_client_positions_latest exists")
    
    # Try to get the view definition
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='view' AND name='vw_client_positions_latest'")
    view_def = cursor.fetchone()[0]
    print(f"View definition: {view_def}")
    
    try:
        # Try to query the view
        cursor.execute("SELECT * FROM vw_client_positions_latest LIMIT 1")
        columns = [description[0] for description in cursor.description]
        print(f"Columns in view: {', '.join(columns)}")
        
        # Check if balance_amount exists in the view
        if 'balance_amount' in columns:
            cursor.execute("SELECT COALESCE(SUM(balance_amount), 0) FROM vw_client_positions_latest")
            total_latest = cursor.fetchone()[0]
            print(f"Total in vw_client_positions_latest: {total_latest}")
        elif 'amount' in columns:
            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM vw_client_positions_latest")
            total_latest = cursor.fetchone()[0]
            print(f"Total in vw_client_positions_latest (amount): {total_latest}")
    except sqlite3.OperationalError as e:
        print(f"Error querying view: {e}")
else:
    print("\nView vw_client_positions_latest does not exist")

conn.close()
