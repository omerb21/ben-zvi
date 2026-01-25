#!/usr/bin/env python
"""
Smoke test for CRM ingestion
Tests that YL files can be loaded and viewed in the clients page
"""

import sys
import logging
import sqlite3
import pandas as pd
from pathlib import Path

# Ensure project root is on sys.path so crm_ingestion can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from crm_ingestion.main import setup_db, process_file
from crm_ingestion import main as ingestion_main

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("crm_ingestion.test")

def create_test_file():
    """Create a test YL Excel file"""
    df = pd.DataFrame({
        'ת.ז': ['123456789', '987654321'],
        'שם עמית': ['ישראל ישראלי', 'שרה כהן'],
        'חשבון': ['ACC001', 'ACC002'],
        'מוצר': ['פנסיה', 'גמל'],
        'שם מסלול': ['מסלול כללי', 'מסלול מניות'],
        'יתרת מסלול': [150000, 75000]
    })
    
    test_file = Path('yl_sample.xlsx')
    df.to_excel(test_file, index=False)
    logger.info(f"Created test file: {test_file}")
    return test_file

def reset_db():
    """Reset the smoke-test database by deleting it if it exists"""
    db_file = Path(ingestion_main.DB_FILE)
    if db_file.exists():
        try:
            db_file.unlink()
            logger.info(f"Deleted existing database: {db_file}")
        except Exception as e:
            logger.error(f"Failed to delete database: {e}")
            return False
    return True

def run_test():
    """Run the smoke test"""
    logger.info("Starting smoke test")
    
    # Use a dedicated smoke-test database so we don't touch the main CRM DB
    ingestion_main.DB_FILE = "crm_smoke.db"

    # Reset database
    if not reset_db():
        logger.error("Failed to reset database")
        return False
    
    # Setup database
    setup_db()
    
    # Create test file
    test_file = create_test_file()
    
    # Process test file
    try:
        snapshot_date = "2025-07-23"
        source = "YL"
        inserted_count = process_file(test_file, source, snapshot_date, verbose=True)
        logger.info(f"Processed test file, inserted {inserted_count} records")
        
        if inserted_count > 0:
            # Verify that records exist in the smoke database snapshot table
            with sqlite3.connect(ingestion_main.DB_FILE) as con:
                count = con.execute("SELECT COUNT(*) FROM snapshot").fetchone()[0]
            logger.info(f"Snapshot table row count: {count}")
            if count >= inserted_count:
                logger.info("Test passed: Records were inserted successfully")
                return True
            else:
                logger.error(
                    f"Test failed: expected at least {inserted_count} rows in snapshot, found {count}"
                )
                return False
        else:
            logger.error("Test failed: No records were inserted")
            return False
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
