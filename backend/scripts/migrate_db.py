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
    
    # Create tables based on current Code models (to support new nullable fields)
    print("Creating schema from code models...")
    # Add parent directory to path to allow importing app
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from app.database import Base
    import app.models  # Register models
    Base.metadata.create_all(bind=dest_engine)

    # Create inspector to check for existing tables
    from sqlalchemy import inspect
    inspector = inspect(dest_engine)
    existing_tables = set(inspector.get_table_names())

    # Copy data
    # Use sorted_tables to ensure creation in dependency order
    for table in source_meta.sorted_tables:
        table_name = table.name
        print(f"Processing table: {table_name}")
        
        # If table wasn't created by create_all (e.g. alembic_version), create it now
        if table_name not in existing_tables:
            try:
                print(f"  - Table {table_name} not found in destination (not in models). Creating from source schema...")
                table.create(dest_engine)
                # Add to existing_tables so we know it exists now
                existing_tables.add(table_name)
            except Exception as e:
                print(f"  - Error creating {table_name}: {e}")
            
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
