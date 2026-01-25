"""Quick inspection script to see client and client_details data.

Usage:
    python tools/inspect_client_details.py
"""

import sqlite3
from pathlib import Path
import sys

# Ensure project root is on sys.path so we can import app.py when running
# this file as: python tools/inspect_client_details.py
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import DB


def main() -> None:
    con = sqlite3.connect(DB)
    cur = con.cursor()

    print("=== Sample clients with non-empty first/last/email/phone ===")
    rows = cur.execute(
        """
        SELECT id, id_canon, name, first_name, last_name, phone, email
        FROM client
        WHERE COALESCE(first_name, '') <> ''
           OR COALESCE(last_name, '') <> ''
           OR COALESCE(phone, '') <> ''
           OR COALESCE(email, '') <> ''
        ORDER BY id
        LIMIT 10
        """
    ).fetchall()
    for r in rows:
        print("client:", r)

    print("\n=== client_details count ===")
    count = cur.execute("SELECT COUNT(*) FROM client_details").fetchone()[0]
    print("client_details rows:", count)

    print("\n=== Sample client_details rows ===")
    rows = cur.execute(
        """
        SELECT client_id, first_name, last_name, date_of_birth, email, employer
        FROM client_details
        ORDER BY client_id
        LIMIT 10
        """
    ).fetchall()
    for r in rows:
        print("details:", r)

    print("\n=== Specific client 55579957 ===")
    row = cur.execute(
        "SELECT id, id_canon, name, first_name, last_name, phone, email FROM client WHERE id_canon = ?",
        ("55579957",),
    ).fetchone()
    print("client 55579957:", row)

    if row:
        cid = row[0]
        rows = cur.execute(
            "SELECT client_id, first_name, last_name, date_of_birth, email, employer FROM client_details WHERE client_id = ?",
            (cid,),
        ).fetchall()
        for r in rows:
            print("client_details 55579957:", r)


if __name__ == "__main__":
    main()
