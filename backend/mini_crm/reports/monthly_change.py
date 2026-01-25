"""Helpers for computing monthly totals and month-over-month changes from snapshot.

This module is pure-python and does not depend on Flask, so it can be used
both from web routes and from CLI/tools.
"""
from __future__ import annotations

from typing import List, Dict, Tuple, Optional
import sqlite3


def get_monthly_totals(db_path: str) -> List[Tuple[str, float]]:
    """Return total assets per month (YYYY-MM) from snapshot.

    Only active rows (is_active = 1) are considered.
    """
    sql = """
        SELECT strftime('%Y-%m', snapshot_date) AS ym,
               COALESCE(SUM(amount), 0.0) AS total_amount
        FROM snapshot
        WHERE is_active = 1
        GROUP BY ym
        ORDER BY ym
    """

    with sqlite3.connect(db_path) as con:
        rows = con.execute(sql).fetchall()

    return [(ym, float(total)) for ym, total in rows if ym is not None]


def compute_month_over_month_changes(
    monthly_totals: List[Tuple[str, float]],
) -> List[Dict[str, Optional[float]]]:
    """Given a list of (month, total), compute month-over-month changes.

    The input is expected to be ordered by month ascending. The result is a list
    of dictionaries with:
      - month: YYYY-MM string
      - total: total assets for that month
      - change: absolute change vs previous month (None for the first month)
      - percent_change: percentage change vs previous month (None if previous total is 0 or missing)
    """
    results: List[Dict[str, Optional[float]]] = []

    prev_total: Optional[float] = None
    for month, total in monthly_totals:
        change: Optional[float]
        percent_change: Optional[float]

        if prev_total is None:
            change = None
            percent_change = None
        else:
            change = total - prev_total
            if prev_total > 0:
                percent_change = (change / prev_total) * 100.0
            else:
                percent_change = None

        results.append(
            {
                "month": month,
                "total": total,
                "change": change,
                "percent_change": percent_change,
            }
        )

        prev_total = total

    return results
