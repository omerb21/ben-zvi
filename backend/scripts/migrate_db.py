import os
import sys
from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateTable

def migrate_data(source_url, dest_url):
    print(f"Connecting to Source DB...")
    source_engine = create_engine(source_url)
    
    print(f"Connecting to Destination DB...")
    dest_engine = create_engine(dest_url)
    
    source_meta = MetaData()
    source_meta.reflect(bind=source_engine)
    
    dest_meta = MetaData()
    
    # Create tables in destination
    print("Creating tables in destination...")
    # Clean slate: Drop all tables in destination to fix schema mismatches
    dest_meta.reflect(bind=dest_engine)
    dest_meta.drop_all(bind=dest_engine)
    
    # We re-reflect source just to be safe (already done above)

    # Copy schema and data
    # Use sorted_tables to ensure creation in dependency order
    for table in source_meta.sorted_tables:
        table_name = table.name
        print(f"Processing table: {table_name}")
        
        # Create table in destination
        try:
            table.create(dest_engine)
            print(f"  - Created table {table_name}")
        except Exception as e:
            print(f"  - Table {table_name} might already exist or error: {e}")
            
        # Copy data
        with source_engine.connect() as src_conn:
            rows = src_conn.execute(table.select()).fetchall()
            if rows:
                # Check if destination table is empty to avoid PK conflicts
                with dest_engine.connect() as check_conn:
                    existing_count = check_conn.execute(table.select()).fetchone()
                    
                if existing_count:
                    print(f"  - Table {table_name} contains data. Skipping data copy to verify safety.")
                else:
                    print(f"  - Copying {len(rows)} rows...")
                    # Insert data
                    with dest_engine.begin() as dest_conn:
                        # We need to construct a list of dicts for the insert
                        data_to_insert = [dict(row._mapping) for row in rows]
                        dest_conn.execute(table.insert(), data_to_insert)
            else:
                print("  - No data to copy.")

    # Fix sequences
    print("Resetting sequences...")
    with dest_engine.begin() as dest_conn:
        for table in source_meta.sorted_tables:
             # Check if table has an 'id' column which usually implies a serial sequence
            if 'id' in table.columns:
                print(f"  - Resetting sequence for {table.name}...")
                try:
                    # Generic Postgres sequence reset
                    dest_conn.execute(
                        text(f"SELECT setval(pg_get_serial_sequence('{table.name}', 'id'), coalesce(max(id), 0) + 1, false) FROM {table.name};")
                    )
                except Exception as e:
                    print(f"    Warning: Could not reset sequence for {table.name}: {e}")

    print("Migration completed successfully!")

if __name__ == "__main__":
    # Get environment variables
    old_db_url = os.environ.get("OLD_DB_URL")
    
    # Try NEW_DB_URL, fallback to DATABASE_URL (standard Railway env var)
    new_db_url = os.environ.get("NEW_DB_URL") or os.environ.get("DATABASE_URL")
    
    if not old_db_url:
        print("Error: OLD_DB_URL environment variable is missing.")
        sys.exit(1)

    if not new_db_url:
        print("Error: NEW_DB_URL or DATABASE_URL environment variable is missing.")
        print("Please set NEW_DB_URL to the destination database URL.")
        sys.exit(1)
        
    print(f"Source: {old_db_url.split('@')[-1]}") # Print non-sensitive part for verification
    print(f"Destination: {new_db_url.split('@')[-1]}")
    
    migrate_data(old_db_url, new_db_url)
