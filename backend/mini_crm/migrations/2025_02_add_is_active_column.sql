-- Migration: Add is_active column to snapshot table
-- Date: 2025-01-28
-- Description: Add is_active column to track active funds and create unique index

-- Add is_active column to snapshot table
ALTER TABLE snapshot ADD COLUMN is_active BOOLEAN DEFAULT 1;

-- Create unique index for snapshot deduplication
CREATE UNIQUE INDEX IF NOT EXISTS snapshot_uq ON snapshot(client_id, fund_number, snapshot_date, source);

-- Update existing snapshots to be active by default
UPDATE snapshot SET is_active = 1 WHERE is_active IS NULL;
