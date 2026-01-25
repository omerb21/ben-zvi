-- Add company column to snapshot table for client reporting
-- Migration: 2025_03_add_company_column.sql

ALTER TABLE snapshot ADD COLUMN company TEXT;

-- Create index for better query performance
CREATE INDEX idx_snapshot_company ON snapshot(company);

-- Update existing records with company names based on source
UPDATE snapshot SET company = 
    CASE source
        WHEN 'YL' THEN 'יהב לוי'
        WHEN 'FNX' THEN 'פניקס'
        WHEN 'MOR' THEN 'מור'
        WHEN 'HAR' THEN 'הראל'
        WHEN 'MIG' THEN 'מגדל'
        WHEN 'KLA' THEN 'כלל'
        WHEN 'PSG' THEN 'פסגות'
        WHEN 'ALT' THEN 'אלטשולר שחם'
        WHEN 'MNR' THEN 'מנורה'
        WHEN 'LEU' THEN 'לאומי'
        WHEN 'EXL' THEN 'אקסלנס'
        WHEN 'IBI' THEN 'IBI'
        WHEN 'ANL' THEN 'אנליסט'
        ELSE source
    END
WHERE company IS NULL;
