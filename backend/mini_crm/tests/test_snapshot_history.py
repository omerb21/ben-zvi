import os, sqlite3, tempfile, pandas as pd, sys
sys.path.insert(0, '.')                       # שייבא את app ו‑insert_rows מהפרויקט
from app import init_db, insert_rows

def _new_db():
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    return db_path

def _base_df(amount):
    """יוצר DataFrame בסיסי עם קרן אחת וסכום משתנה"""
    return pd.DataFrame(
        {
            "client_name": ["בדיקה יוסף"],
            "id_canon": ["123456789"],
            "fund_number": ["TEST‑001"],
            "fund_code": ["TST001"],
            "fund_type": ["מניות"],
            "fund_name": ["קרן בדיקה"],
            "accumulated_amount": [amount],
            "client_key": ["בדיקה יוסף_123456789"],
        }
    )

def _count_snap(con):
    return con.execute("SELECT COUNT(*) FROM snapshot").fetchone()[0]

def test_monthly_history_kept():
    # ➊ DB חדש בכל ריצה
    db_path = _new_db()
    import app
    app.DB = db_path
    init_db()

    # ➋ יוני – סכום 1 000
    df_jun = _base_df(1000)
    insert_rows(df_jun, source="TEST", snap_date="2025‑06‑15")

    with sqlite3.connect(db_path) as con:
        assert _count_snap(con) == 1

    # ➌ יולי – סכום 2 000
    df_jul = _base_df(2000)
    insert_rows(df_jul, source="TEST", snap_date="2025‑07‑20")

    with sqlite3.connect(db_path) as con:
        c = con.execute(
            "SELECT snapshot_date, amount FROM snapshot ORDER BY snapshot_date"
        ).fetchall()
        # אמורים להיות 2 חודשים שונים, כל אחד עם ערך אחר
        assert len(c) == 2
        assert c[0][0] == "2025‑06‑01" and c[0][1] == 1000.0
        assert c[1][0] == "2025‑07‑01" and c[1][1] == 2000.0


def test_aggregate_multiple_tracks_same_fund():
    """Verify that multiple rows for the same client+fund in the same month are summed."""
    db_path = _new_db()
    import app
    app.DB = db_path
    init_db()

    # Two rows for the same client and fund_number in the same month
    test_data = pd.DataFrame(
        {
            "client_name": ["לקוח בדיקה", "לקוח בדיקה"],
            "id_canon": ["111111111", "111111111"],
            "fund_number": ["FUND123", "FUND123"],
            "fund_code": ["CODE1", "CODE1"],
            "fund_type": ["מניות", "מניות"],
            "fund_name": ["קופה מצטברת", "קופה מצטברת"],
            "accumulated_amount": [1000.0, 2000.0],
            "client_key": ["לקוח בדיקה_111111111", "לקוח בדיקה_111111111"],
        }
    )

    insert_rows(test_data, source="TEST", snap_date="2025‑08‑15")

    with sqlite3.connect(db_path) as con:
        rows = con.execute(
            "SELECT snapshot_date, amount FROM snapshot WHERE fund_number = ?",
            ("FUND123",),
        ).fetchall()

    # Should be a single row for the month with summed amount
    assert len(rows) == 1
    assert rows[0][0] == "2025‑08‑01"
    assert rows[0][1] == 3000.0
