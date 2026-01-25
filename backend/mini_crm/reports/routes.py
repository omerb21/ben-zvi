import csv
import io
import sqlite3
import datetime as dt
from flask import current_app, request, Response
from . import reports_bp
from reports.monthly_change import get_monthly_totals, compute_month_over_month_changes

def get_db_path():
    """Get database path from app config or default."""
    return current_app.config.get("DB", "crm.db")

@reports_bp.route("/funds")
def funds_csv():
    """Export funds data for a specific month as CSV."""
    month = request.args.get("month")  # YYYY-MM
    if not month:
        return {"error": "month parameter required (format: YYYY-MM)"}, 400
    
    try:
        snap_date = dt.datetime.strptime(month, "%Y-%m").date().replace(day=1)
    except Exception:
        return {"error": "month parameter format YYYY-MM"}, 400

    sql = """
     SELECT c.name, c.id_canon, s.fund_number, s.fund_name, s.fund_type,
            s.amount, s.source 
     FROM snapshot s
     JOIN client c ON c.id = s.client_id
     WHERE s.snapshot_date = ?
     ORDER BY c.name
    """
    
    with sqlite3.connect(get_db_path()) as con:
        rows = con.execute(sql, (snap_date.isoformat(),)).fetchall()

    # Stream as CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["client_name", "id_canon", "fund_number", "fund_name",
                     "fund_type", "amount", "source"])
    writer.writerows(rows)
    csv_data = output.getvalue()
    
    return Response(csv_data,
          mimetype="text/csv",
          headers={"Content-Disposition":
                   f"attachment;filename=funds_{month}.csv"})


@reports_bp.route("/monthly_change")
def monthly_change_csv():
    """Export monthly totals and month-over-month changes as CSV."""
    db_path = get_db_path()
    monthly_totals = get_monthly_totals(db_path)
    changes = compute_month_over_month_changes(monthly_totals)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["month", "total", "change", "percent_change"])

    for row in changes:
        month = row.get("month", "")
        total = row.get("total", 0) or 0
        change = row.get("change")
        percent_change = row.get("percent_change")

        change_str = "" if change is None else str(change)
        pct_str = "" if percent_change is None else f"{percent_change:.2f}"

        writer.writerow([month, total, change_str, pct_str])

    csv_data = output.getvalue()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=monthly_change.csv"},
    )
