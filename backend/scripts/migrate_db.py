import os
import sys
from sqlalchemy import create_engine, MetaData, Table
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
    # We reflect the source tables and recreate them in the destination
    # Note: specific constraints or types might need adjustment if DB versions differ significantly,
    # but for standard Postgres to Postgres it should work fine.
    # However, a safer bet for pure data copy if schema exists is just clearing and copying.
    # But if schema doesn't exist, we need to create it.
    # For simplicity, we assume we want to replicate the schema too.
    
    # Dropping all tables in destination to ensure clean slate (OPTIONAL - BE CAREFUL)
    # dest_meta.reflect(bind=dest_engine)
    # dest_meta.drop_all(bind=dest_engine)

    # Copy schema and data
    for table_name, table in source_meta.tables.items():
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
                print(f"  - Copying {len(rows)} rows...")
                # Insert data in batches or all at once
                # For large datasets, batching is better. Here we do simple insert.
                # SQLAlchemy Core insert
                with dest_engine.begin() as dest_conn:
                    # We need to construct a list of dicts for the insert
                    data_to_insert = [dict(row._mapping) for row in rows]
                    dest_conn.execute(table.insert(), data_to_insert)
            else:
                print("  - No data to copy.")

    print("Migration completed successfully!")

if __name__ == "__main__":
    old_db_url = os.environ.get("OLD_DB_URL")
    new_db_url = os.environ.get("NEW_DB_URL")
    
    if not old_db_url or not new_db_url:
        print("Error: Please set OLD_DB_URL and NEW_DB_URL environment variables.")
        sys.exit(1)
        
    migrate_data(old_db_url, new_db_url)
