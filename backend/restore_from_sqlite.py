import os
import sys
from sqlalchemy import create_engine, MetaData, text

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv(override=True)

def restore_from_sqlite():
    # Source: Local SQLite
    sqlite_url = "sqlite:///./unified_crm_justification.db"
    
    # Destination: Railway PostgreSQL
    pg_url = os.getenv("DATABASE_URL")
    
    print(f"Source: SQLite (local)")
    print(f"Destination: {pg_url.split('@')[-1]}")
    
    source_engine = create_engine(sqlite_url)
    dest_engine = create_engine(pg_url)
    
    source_meta = MetaData()
    source_meta.reflect(bind=source_engine)
    
    print(f"\nFound {len(source_meta.tables)} tables in SQLite backup")
    
    # Import models to create schema
    sys.path.append(os.path.dirname(__file__))
    from app.database import Base
    import app.models
    
    print("Creating PostgreSQL schema...")
    Base.metadata.create_all(bind=dest_engine)
    
    # Reflect destination
    dest_meta = MetaData()
    dest_meta.reflect(bind=dest_engine)
    
    # Copy data table by table
    for table in source_meta.sorted_tables:
        table_name = table.name
        
        # Skip if table doesn't exist in destination
        if table_name not in dest_meta.tables:
            print(f"Skipping {table_name} (not in destination schema)")
            continue
            
        print(f"\nProcessing {table_name}...")
        
        target_table = dest_meta.tables[table_name]
        target_columns = set(c.name for c in target_table.columns)
        
        # Read from SQLite
        with source_engine.connect() as src_conn:
            rows = src_conn.execute(table.select()).fetchall()
            
            if not rows:
                print(f"  No data to copy")
                continue
                
            print(f"  Copying {len(rows)} rows...")
            
            # Filter columns
            clean_data = []
            for row in rows:
                row_dict = dict(row._mapping)
                filtered_row = {k: v for k, v in row_dict.items() if k in target_columns}
                clean_data.append(filtered_row)
            
            # Insert to PostgreSQL
            with dest_engine.begin() as dest_conn:
                dest_conn.execute(target_table.insert(), clean_data)
    
    # Reset sequences
    print("\nResetting sequences...")
    with dest_engine.begin() as conn:
        for table in dest_meta.sorted_tables:
            if 'id' in table.columns:
                try:
                    conn.execute(text(
                        f"SELECT setval(pg_get_serial_sequence('{table.name}', 'id'), "
                        f"coalesce(max(id), 0) + 1, false) FROM {table.name};"
                    ))
                    print(f"  Reset sequence for {table.name}")
                except Exception as e:
                    print(f"  Warning: {table.name}: {e}")
    
    print("\n✅ Restore completed!")

if __name__ == "__main__":
    restore_from_sqlite()
