import os
import sys
# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv(override=True)

from sqlalchemy import create_engine, text

def check_db():
    url = os.getenv("DATABASE_URL")
    print(f"Checking connection to: {url.split('@')[-1]}") # Print safe part
    
    try:
        # Add 5 second timeout
        engine = create_engine(url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            print("Successfully connected!")
            
            # Check version
            ver = conn.execute(text("SELECT version();")).fetchone()
            print(f"DB Version: {ver[0]}")
            
            # Check tables
            print("\nChecking tables:")
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';"))
            tables = [row[0] for row in result.fetchall()]
            print(f"Found {len(tables)} tables: {tables}")
            
            if 'client' in tables:
                count = conn.execute(text("SELECT count(*) FROM client;")).scalar()
                print(f"\nClient count: {count}")
            else:
                print("\nCRITICAL: 'client' table NOT found!")

    except Exception as e:
        print(f"\nConnection failed: {e}")

if __name__ == "__main__":
    check_db()
