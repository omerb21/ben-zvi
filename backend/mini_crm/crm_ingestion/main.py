#!/usr/bin/env python
"""
CRM Data Ingestion Module
Loads client data from Excel files into the CRM database
"""

import argparse
import logging
import sys
from pathlib import Path
import pandas as pd
import sqlite3
import os

# Import loaders
from crm_ingestion.loaders import yl_loader
from crm_ingestion.loaders import fnx_loader
from crm_ingestion.loaders import as_loader
from crm_ingestion.loaders import mor_loader
from crm_ingestion.loaders import anlst_loader
from crm_ingestion.loaders import nfty_loader
from crm_ingestion.loaders import dash_loader

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("crm_ingestion")

# Database configuration
DB_FILE = os.environ.get("CRM_DB", "crm.db")

class MissingColumnsError(Exception):
    """Exception raised when required columns are missing from the input file."""
    pass

def setup_db():
    """Initialize the database tables if they don't exist"""
    with sqlite3.connect(DB_FILE) as con:
        con.executescript(
            """
            create table if not exists client (
                id integer primary key,
                id_canon text unique,
                personal_number text,
                name text
            );
            create table if not exists snapshot (
                id integer primary key,
                client_id integer,
                fund_code text,
                fund_number text,
                fund_type text,
                fund_name text,
                snapshot_date text,
                amount real,
                source text,
                foreign key(client_id) references client(id)
            );
            """
        )
    logger.info(f"Database initialized: {DB_FILE}")

def get_loader(source):
    """Get the appropriate loader for the specified data source"""
    if source == "YL":
        return yl_loader
    elif source == "FNX":
        return fnx_loader
    elif source == "AS":
        return as_loader
    elif source == "MOR":
        return mor_loader
    elif source == "ANLST":
        return anlst_loader
    elif source == "NFTY":
        return nfty_loader
    elif source == "DASH":
        return dash_loader
    # Add other source loaders as needed
    raise ValueError(f"Unknown source: {source}")

def validate_dataframe(df, required_columns):
    """Validate that the DataFrame has all required columns"""
    df_columns = set(df.columns)
    missing_columns = [col for col in required_columns if col not in df_columns]
    
    if missing_columns:
        error_msg = f"Missing required columns: {', '.join(missing_columns)}"
        logger.error(error_msg)
        raise MissingColumnsError(error_msg)

def map_dataframe(df, column_mapping):
    """Map source columns to target columns"""
    mapped_df = pd.DataFrame()
    
    for source_col, target_col in column_mapping.items():
        if source_col in df.columns:
            mapped_df[target_col] = df[source_col]
        else:
            logger.warning(f"Column '{source_col}' not found in input file")
    
    return mapped_df

def insert_data(df, source, snapshot_date):
    """Insert data into the database"""
    inserted_count = 0
    skipped_count = 0
    
    with sqlite3.connect(DB_FILE) as con:
        for idx, row in df.iterrows():
            try:
                # Log each row being processed
                logger.debug(f"Processing row {idx+1}: {row.to_dict()}")
                
                # Insert or get client
                cid = con.execute(
                    "INSERT OR IGNORE INTO client(id_canon, name) VALUES(?, ?)",
                    (row["id_canon"], row["client_name"])
                ).lastrowid
                
                if not cid:  # Client already exists
                    cid = con.execute(
                        "SELECT id FROM client WHERE id_canon=?", 
                        (row["id_canon"],)
                    ).fetchone()[0]
                
                # Get the fund_number for this row (if available)
                fund_number = row.get("fund_number", "")
                
                # Check if this fund already exists for this client
                existing_fund = None
                if fund_number:
                    existing_fund = con.execute(
                        """SELECT id FROM snapshot 
                           WHERE client_id = ? AND fund_number = ? AND source = ?""",
                        (cid, fund_number, source)
                    ).fetchone()
                
                # Only insert if the fund doesn't already exist for this client
                if not existing_fund:
                    # Insert snapshot
                    con.execute(
                        """
                        INSERT INTO snapshot(
                            client_id, fund_code, fund_number, fund_type, fund_name, snapshot_date, amount, source
                        ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            cid, 
                            row.get("fund_code", ""),  # Make fund_code optional
                            fund_number,  # Use the fund_number we extracted
                            row.get("fund_type", ""), 
                            row.get("fund_name", ""), 
                            snapshot_date, 
                            row["accumulated_amount"], 
                            source
                        )
                    )
                    inserted_count += 1
                else:
                    skipped_count += 1
                    logger.debug(f"Skipping duplicate fund {fund_number} for client {row['id_canon']}")
                
            except Exception as e:
                logger.error(f"Error processing row {idx+1}: {e}")
                
    logger.info(f"Inserted {inserted_count} records into the database (skipped {skipped_count} duplicates)")
    return inserted_count

def process_file(file_path, source, snapshot_date, verbose=False):
    """Process an Excel file and load it into the database"""
    if verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info(f"Processing file: {file_path}")
    logger.info(f"Source: {source}, Snapshot date: {snapshot_date}")
    
    try:
        # Read the Excel file
        df = pd.read_excel(file_path)
        logger.info(f"Read {len(df)} rows from {file_path}")
        
        # Get the appropriate loader for the source
        loader = get_loader(source)
        
        # Transform data using the loader
        mapped_df = loader.load_and_transform(df, snapshot_date)
        
        # Insert data into database
        inserted_count = insert_data(mapped_df, source, snapshot_date)
        
        return inserted_count
        
    except MissingColumnsError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise

def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description="CRM Data Ingestion Tool")
    parser.add_argument("file", help="Excel file to process")
    parser.add_argument("--date", required=True, help="Snapshot date (YYYY-MM-DD)")
    parser.add_argument("--source", required=True, help="Data source identifier")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    try:
        # Validate file exists
        file_path = Path(args.file)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return 1
        
        # Setup database
        setup_db()
        
        # Process file
        inserted = process_file(
            file_path, 
            args.source, 
            args.date, 
            args.verbose
        )
        
        logger.info(f"Successfully processed {file_path} - inserted {inserted} records")
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
