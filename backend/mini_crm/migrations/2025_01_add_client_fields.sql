-- Migration: Add extended client fields
-- Date: 2025-01-28
-- Description: Add comprehensive client information fields to client table

-- Add new fields to client table
ALTER TABLE client ADD COLUMN first_name TEXT;
ALTER TABLE client ADD COLUMN last_name TEXT;
ALTER TABLE client ADD COLUMN birth_date DATE;
ALTER TABLE client ADD COLUMN street TEXT;
ALTER TABLE client ADD COLUMN house_number TEXT;
ALTER TABLE client ADD COLUMN city TEXT;
ALTER TABLE client ADD COLUMN phone TEXT;
ALTER TABLE client ADD COLUMN email TEXT;
ALTER TABLE client ADD COLUMN gender TEXT;
ALTER TABLE client ADD COLUMN marital_status TEXT;
ALTER TABLE client ADD COLUMN birth_country TEXT;
ALTER TABLE client ADD COLUMN employer_name TEXT;
ALTER TABLE client ADD COLUMN employer_hp TEXT;
ALTER TABLE client ADD COLUMN employer_address TEXT;
ALTER TABLE client ADD COLUMN employer_phone TEXT;

-- Add index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_client_email ON client(email);

-- Add index on phone for faster lookups
CREATE INDEX IF NOT EXISTS idx_client_phone ON client(phone);

-- Add composite index for name searches
CREATE INDEX IF NOT EXISTS idx_client_names ON client(first_name, last_name);
