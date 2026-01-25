#!/usr/bin/env python3
"""
Script to mark funds as closed (is_active=0) if not seen for specified months.
Usage: python tools/mark_closed_funds.py [months]
"""

import sqlite3
import datetime as dt
import sys
import logging
import argparse
from pathlib import Path
import os

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database path
DB = os.environ.get("CRM_DB", "crm.db")


def close_old_funds(months: int = 2, dry_run: bool = False):
    """
    Mark funds as inactive if they haven't appeared in the last N months.
    
    Args:
        months: Number of months to look back (default: 2)
    """
    today = dt.date.today().replace(day=1)  # Normalize to first of month
    threshold = (today - dt.timedelta(days=months * 31)).replace(day=1)
    
    logger.info(f"Marking funds as closed if not seen since: {threshold}")
    
    with sqlite3.connect(DB) as con:
        with con:
            # Get count of funds that will be marked as closed
            closed_count = con.execute("""
                SELECT COUNT(DISTINCT client_id || '|' || fund_number || '|' || source)
                FROM snapshot 
                WHERE is_active = 1
                  AND (client_id, fund_number, source) NOT IN (
                      SELECT client_id, fund_number, source
                      FROM snapshot
                      WHERE snapshot_date >= ?
                  )
            """, (threshold.isoformat(),)).fetchone()[0]
            
            if closed_count == 0:
                logger.info("No funds to mark as closed")
                return 0
            
            if dry_run:
                logger.info("Dry-run mode – skipping DB update")
                logger.info(f"Would mark {closed_count} unique funds as closed")
                logger.info("Dry-run only – no DB changes were made")
                
                # Show details of what would be closed
                funds_to_close = con.execute("""
                    SELECT DISTINCT c.name, s.fund_number, s.source, MAX(s.snapshot_date) as last_seen
                    FROM snapshot s
                    JOIN client c ON c.id = s.client_id
                    WHERE s.is_active = 1
                      AND (s.client_id, s.fund_number, s.source) NOT IN (
                          SELECT client_id, fund_number, source
                          FROM snapshot
                          WHERE snapshot_date >= ?
                      )
                    GROUP BY c.name, s.fund_number, s.source
                    ORDER BY c.name, s.fund_number
                """, (threshold.isoformat(),)).fetchall()
                
                logger.info("Funds that would be marked as closed:")
                for client_name, fund_number, source, last_seen in funds_to_close:
                    logger.info(f"  - {client_name}: {fund_number} ({source}) - last seen: {last_seen}")
                    
                return closed_count
            else:
                # Mark funds as closed
                con.execute("""
                    UPDATE snapshot SET is_active = 0
                    WHERE is_active = 1
                      AND (client_id, fund_number, source) NOT IN (
                          SELECT client_id, fund_number, source
                          FROM snapshot
                          WHERE snapshot_date >= ?
                      )
                """, (threshold.isoformat(),))
                
                # Get count of affected rows
                affected_rows = con.total_changes
                
                logger.info(f"✓ Marked {closed_count} unique funds as closed (affected {affected_rows} snapshot records)")
                logger.info(f"✓ Funds not seen since {threshold} are now marked as inactive")
                
                return closed_count


def get_fund_status_summary():
    """Get summary of active vs inactive funds."""
    with sqlite3.connect(DB) as con:
        # Get active funds count
        active_count = con.execute("""
            SELECT COUNT(DISTINCT client_id || '|' || fund_number || '|' || source)
            FROM snapshot 
            WHERE is_active = 1
        """).fetchone()[0]
        
        # Get inactive funds count
        inactive_count = con.execute("""
            SELECT COUNT(DISTINCT client_id || '|' || fund_number || '|' || source)
            FROM snapshot 
            WHERE is_active = 0
        """).fetchone()[0]
        
        logger.info(f"Fund status summary:")
        logger.info(f"  - Active funds: {active_count}")
        logger.info(f"  - Inactive funds: {inactive_count}")
        logger.info(f"  - Total funds: {active_count + inactive_count}")
        
        return active_count, inactive_count


def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Mark old funds as closed')
    parser.add_argument('--months', type=int, default=2, 
                       help='Number of months threshold (default: 2)')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Simulate only - no DB changes will be made')
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info(f"Starting fund closure process in DRY-RUN mode with {args.months} months threshold")
    else:
        logger.info(f"Starting fund closure process with {args.months} months threshold")
    
    # Get initial status
    logger.info("Initial fund status:")
    get_fund_status_summary()
    
    # Mark closed funds
    closed_count = close_old_funds(args.months, args.dry_run)
    
    if not args.dry_run:
        # Get final status only if we actually made changes
        logger.info("Final fund status:")
        get_fund_status_summary()
    
    logger.info("Fund closure process completed successfully")


if __name__ == "__main__":
    main()
