"""
Create client_positions_monthly table and sync data to snapshot.
This implements Branch A solution where dashboard reads from snapshot.
"""
import sqlite3
import datetime
import sys
import os

def log_message(message):
    """Log message to console and log file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    print(formatted_message)
    
    with open("sync_to_snapshot.log", "a", encoding="utf-8") as log_file:
        log_file.write(formatted_message + "\n")

def main():
    """Create client_positions_monthly table and sync to snapshot."""
    try:
        # Connect to the database
        db_path = os.environ.get("CRM_DB", "crm.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        log_message("CREATING CLIENT_POSITIONS_MONTHLY AND SYNCING TO SNAPSHOT")
        log_message("=" * 50)
        
        # Check if client_positions_monthly exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='client_positions_monthly'")
        if not cursor.fetchone():
            log_message("Creating client_positions_monthly table...")
            
            # Create the client_positions_monthly table
            cursor.execute("""
                CREATE TABLE client_positions_monthly (
                    id INTEGER PRIMARY KEY,
                    client_id INTEGER,
                    product_id TEXT,
                    as_of_month TEXT,  -- YYYY-MM-01 format
                    balance_amount REAL CHECK (balance_amount >= 0),
                    fund_code TEXT,
                    fund_number TEXT,
                    fund_type TEXT,
                    fund_name TEXT,
                    source TEXT,
                    company TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY(client_id) REFERENCES client(id),
                    UNIQUE(client_id, product_id, as_of_month)
                )
            """)
            
            # Create index for performance
            cursor.execute("""
                CREATE INDEX idx_client_positions_monthly_client_id
                ON client_positions_monthly(client_id)
            """)
            
            log_message("Table client_positions_monthly created successfully")
        else:
            log_message("Table client_positions_monthly already exists")
        
        # Check if we have data in snapshot
        cursor.execute("SELECT COUNT(*) FROM snapshot")
        snapshot_count = cursor.fetchone()[0]
        log_message(f"Records in snapshot: {snapshot_count}")
        
        if snapshot_count > 0:
            # Migrate data from snapshot to client_positions_monthly
            log_message("Migrating data from snapshot to client_positions_monthly...")
            
            # Get current month in YYYY-MM-01 format
            current_month = datetime.datetime.now().replace(day=1).strftime("%Y-%m-%d")
            
            # Insert data from snapshot to client_positions_monthly
            cursor.execute("""
                INSERT OR IGNORE INTO client_positions_monthly
                (client_id, product_id, as_of_month, balance_amount, fund_code, 
                 fund_number, fund_type, fund_name, source, company, is_active)
                SELECT 
                    client_id,
                    fund_number AS product_id,
                    ? AS as_of_month,
                    amount AS balance_amount,
                    fund_code,
                    fund_number,
                    fund_type,
                    fund_name,
                    source,
                    company,
                    is_active
                FROM snapshot
                WHERE is_active = 1
            """, (current_month,))
            
            inserted_count = cursor.rowcount
            log_message(f"Inserted {inserted_count} records into client_positions_monthly")
            conn.commit()
        
        # Check data in client_positions_monthly
        cursor.execute("SELECT COUNT(*) FROM client_positions_monthly")
        monthly_count = cursor.fetchone()[0]
        log_message(f"Records in client_positions_monthly: {monthly_count}")
        
        # Check data in snapshot
        cursor.execute("SELECT COUNT(*) FROM snapshot")
        snapshot_count = cursor.fetchone()[0]
        log_message(f"Records in snapshot before sync: {snapshot_count}")
        
        # Create a backup of the snapshot table
        log_message("Creating backup of snapshot table...")
        cursor.execute("DROP TABLE IF EXISTS snapshot_backup")
        cursor.execute("CREATE TABLE snapshot_backup AS SELECT * FROM snapshot")
        cursor.execute("SELECT COUNT(*) FROM snapshot_backup")
        backup_count = cursor.fetchone()[0]
        log_message(f"Backup created with {backup_count} records")
        
        # Clear the snapshot table
        log_message("Clearing snapshot table...")
        cursor.execute("DELETE FROM snapshot")
        
        # Insert latest data from client_positions_monthly into snapshot
        log_message("Inserting latest data from client_positions_monthly into snapshot...")
        
        # Get the column names from both tables to ensure proper mapping
        cursor.execute("PRAGMA table_info(client_positions_monthly)")
        monthly_columns = [row['name'] for row in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(snapshot)")
        snapshot_columns = [row['name'] for row in cursor.fetchall()]
        
        # Map column names between tables
        column_mapping = {
            'client_id': 'client_id',
            'fund_code': 'fund_code',
            'fund_number': 'fund_number',
            'fund_type': 'fund_type',
            'fund_name': 'fund_name',
            'source': 'source',
            'company': 'company',
            'is_active': 'is_active',
            'balance_amount': 'amount',
            'as_of_month': 'snapshot_date'
        }
        
        # Find common columns between the two tables using the mapping
        common_columns = []
        for monthly_col, snapshot_col in column_mapping.items():
            if monthly_col in monthly_columns and snapshot_col in snapshot_columns:
                common_columns.append((monthly_col, snapshot_col))
        
        log_message(f"Common columns mapped: {len(common_columns)}")
        
        # Create column lists for the SQL query
        snapshot_cols = ', '.join([snapshot_col for _, snapshot_col in common_columns])
        monthly_cols = ', '.join([f'm.{monthly_col}' for monthly_col, _ in common_columns])
        
        # Create a WITH clause to get the latest records for each client/product
        insert_sql = f"""
        WITH latest AS (
            SELECT client_id, product_id, MAX(as_of_month) AS as_of_month
            FROM client_positions_monthly
            GROUP BY client_id, product_id
        )
        INSERT INTO snapshot ({snapshot_cols})
        SELECT {monthly_cols}
        FROM client_positions_monthly m
        JOIN latest l
            ON l.client_id = m.client_id
            AND l.product_id = m.product_id
            AND l.as_of_month = m.as_of_month
        """
        
        cursor.execute(insert_sql)
        conn.commit()
        
        # Check data in snapshot after sync
        cursor.execute("SELECT COUNT(*) FROM snapshot")
        new_snapshot_count = cursor.fetchone()[0]
        log_message(f"Records in snapshot after sync: {new_snapshot_count}")
        
        # Calculate portfolio total from snapshot
        cursor.execute("SELECT COALESCE(SUM(amount), 0) AS portfolio_total FROM snapshot")
        snapshot_total = cursor.fetchone()['portfolio_total']
        log_message(f"Portfolio total from snapshot: {snapshot_total}")
        
        # Calculate portfolio total from client_positions_monthly (latest records)
        cursor.execute("""
        WITH latest AS (
            SELECT client_id, product_id, MAX(as_of_month) AS as_of_month
            FROM client_positions_monthly
            GROUP BY client_id, product_id
        )
        SELECT COALESCE(SUM(m.balance_amount), 0) AS portfolio_total
        FROM client_positions_monthly m
        JOIN latest l
            ON l.client_id = m.client_id
            AND l.product_id = m.product_id
            AND l.as_of_month = m.as_of_month
        """)
        monthly_total = cursor.fetchone()['portfolio_total']
        log_message(f"Portfolio total from client_positions_monthly (latest): {monthly_total}")
        
        log_message("\nSync completed successfully!")
        
        # Close connection
        conn.close()
        
    except Exception as e:
        log_message(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
