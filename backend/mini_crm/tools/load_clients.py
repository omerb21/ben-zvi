#!/usr/bin/env python3
"""
One-time client data loader from Clients.xlsx
Usage: python tools/load_clients.py uploads/Clients.xlsx
"""

import pandas as pd
import sqlite3
import re
import sys
import logging
from datetime import datetime
from pathlib import Path
import os

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from crm_ingestion.utils.normalize import normalize_id, normalize_name

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database path
DB = os.environ.get("CRM_DB", "crm.db")

# Column mapping for Clients.xlsx (based on actual file structure)
COLUMN_MAP = {
    "פרטי": "first_name",
    "משפחה": "last_name", 
    "תז": "id_canon",
    "ת לידה": "birth_date",
    "רחוב": "street",
    "מספר": "house_number",
    "עיר": "city",
    "טלפון": "phone",
    "דואל": "email",
    "מין": "gender",
    "סטטוס": "marital_status",
    "ארץ לידה": "birth_country",
    "מעסיק": "employer_name",
    "חפ מעסיק": "employer_hp",
    "כתובת מעסיק": "employer_address",
    "טלפון מעסיק": "employer_phone"
}


def split_full_name(full_name):
    """Split full name into first and last name."""
    if not full_name or pd.isna(full_name):
        return "", ""
    
    parts = str(full_name).strip().split()
    if len(parts) == 0:
        return "", ""
    elif len(parts) == 1:
        return parts[0], ""
    else:
        return parts[0], " ".join(parts[1:])


def clean_date(date_value):
    """Clean and format date value to YYYY-MM-DD."""
    if pd.isna(date_value) or not date_value:
        return None
    
    try:
        # Try to parse as datetime
        if isinstance(date_value, str):
            # Handle various date formats
            for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y"]:
                try:
                    return datetime.strptime(date_value, fmt).strftime("%Y-%m-%d")
                except ValueError:
                    continue
        elif hasattr(date_value, 'strftime'):
            return date_value.strftime("%Y-%m-%d")
        
        # If all else fails, try pandas
        return pd.to_datetime(date_value, dayfirst=True).strftime("%Y-%m-%d")
    except:
        logger.warning(f"Could not parse date: {date_value}")
        return None


def clean_phone(phone):
    """Clean phone number - remove non-digits except +."""
    if pd.isna(phone) or not phone:
        return None
    
    phone = str(phone).strip()
    # Keep only digits, +, -, and spaces
    phone = re.sub(r'[^\d+\-\s]', '', phone)
    return phone if phone else None


def normalize_gender(gender):
    """Normalize gender values."""
    if pd.isna(gender) or not gender:
        return None
    
    gender = str(gender).strip().lower()
    if gender in ['ז', 'זכר', 'male', 'm']:
        return "זכר"
    elif gender in ['נ', 'נקבה', 'female', 'f']:
        return "נקבה"
    
    return gender


def normalize_marital_status(status):
    """Normalize marital status values."""
    if pd.isna(status) or not status:
        return None
    
    status = str(status).strip()
    # Add common mappings as needed
    status_map = {
        "נשוי": "נשוי/נשואה",
        "נשואה": "נשוי/נשואה", 
        "רווק": "רווק/רווקה",
        "רווקה": "רווק/רווקה",
        "גרוש": "גרוש/גרושה",
        "גרושה": "גרוש/גרושה",
        "אלמן": "אלמן/אלמנה",
        "אלמנה": "אלמן/אלמנה"
    }
    
    return status_map.get(status, status)


def load_and_process_clients(file_path):
    """Load and process client data from Excel file."""
    logger.info(f"Loading client data from: {file_path}")
    
    # Read Excel file
    try:
        df = pd.read_excel(file_path)
        logger.info(f"Loaded {len(df)} rows from Excel file")
    except Exception as e:
        logger.error(f"Failed to read Excel file: {e}")
        return None
    
    # Check available columns
    logger.info(f"Available columns: {list(df.columns)}")
    
    # Map columns (only use columns that exist)
    available_cols = {}
    for excel_col, db_col in COLUMN_MAP.items():
        if excel_col in df.columns:
            available_cols[excel_col] = db_col
        else:
            logger.warning(f"Column '{excel_col}' not found in Excel file")
    
    # Rename columns
    df = df.rename(columns=available_cols)
    
    # Keep only mapped columns
    df = df[[col for col in available_cols.values() if col in df.columns]]
    
    # Process data
    logger.info("Processing client data...")
    
    # Handle full name splitting if needed
    if 'full_name' in df.columns and 'first_name' not in df.columns:
        logger.info("Splitting full names into first and last names")
        df[['first_name', 'last_name']] = df['full_name'].apply(
            lambda x: pd.Series(split_full_name(x))
        )
    
    # Clean and normalize data
    if 'id_canon' in df.columns:
        df['id_canon'] = df['id_canon'].astype(str).apply(normalize_id)
    
    if 'birth_date' in df.columns:
        df['birth_date'] = df['birth_date'].apply(clean_date)
    
    if 'phone' in df.columns:
        df['phone'] = df['phone'].apply(clean_phone)
    
    if 'gender' in df.columns:
        df['gender'] = df['gender'].apply(normalize_gender)
    
    if 'marital_status' in df.columns:
        df['marital_status'] = df['marital_status'].apply(normalize_marital_status)
    
    # Create client_key for consistency
    if 'first_name' in df.columns and 'last_name' in df.columns and 'id_canon' in df.columns:
        df['name'] = df['first_name'] + ' ' + df['last_name']
        df['client_key'] = df.apply(
            lambda row: normalize_name(row['name']) + "|" + str(row['id_canon']), 
            axis=1
        )
    
    logger.info(f"Processed {len(df)} client records")
    return df


def insert_clients_to_db(df):
    """Insert or update client records in database."""
    if df is None or len(df) == 0:
        logger.error("No data to insert")
        return 0
    
    logger.info("Inserting/updating clients in database...")
    
    # Define the fields we want to insert/update
    client_fields = [
        'id_canon', 'name', 'first_name', 'last_name', 'birth_date',
        'street', 'house_number', 'city', 'phone', 'email',
        'gender', 'marital_status', 'birth_country',
        'employer_name', 'employer_hp', 'employer_address', 'employer_phone'
    ]
    
    # Filter to only fields that exist in the DataFrame
    available_fields = [field for field in client_fields if field in df.columns]
    
    # Prepare SQL
    placeholders = ', '.join([f':{field}' for field in available_fields])
    update_set = ', '.join([f'{field}=excluded.{field}' for field in available_fields if field != 'id_canon'])
    
    sql = f"""
        INSERT INTO client ({', '.join(available_fields)})
        VALUES ({placeholders})
        ON CONFLICT(id_canon) DO UPDATE SET
            {update_set}
    """
    
    inserted_count = 0
    updated_count = 0
    error_count = 0
    
    with sqlite3.connect(DB) as con:
        with con:
            for _, row in df.iterrows():
                try:
                    # Prepare parameters
                    params = {field: row.get(field) for field in available_fields}
                    
                    # Check if client exists
                    existing = con.execute(
                        "SELECT id FROM client WHERE id_canon = ?", 
                        (params['id_canon'],)
                    ).fetchone()
                    
                    # Execute insert/update
                    con.execute(sql, params)
                    
                    if existing:
                        updated_count += 1
                    else:
                        inserted_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing client {row.get('id_canon', 'unknown')}: {e}")
                    error_count += 1
    
    logger.info(f"Database operation completed:")
    logger.info(f"  - Inserted: {inserted_count} new clients")
    logger.info(f"  - Updated: {updated_count} existing clients")
    logger.info(f"  - Errors: {error_count}")
    
    return inserted_count + updated_count


def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python tools/load_clients.py <path_to_clients.xlsx>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)
    
    # Load and process data
    df = load_and_process_clients(file_path)
    
    if df is None:
        logger.error("Failed to load client data")
        sys.exit(1)
    
    # Insert to database
    processed_count = insert_clients_to_db(df)
    
    logger.info(f"✓ Client loading completed. Processed {processed_count} records.")


if __name__ == "__main__":
    main()
