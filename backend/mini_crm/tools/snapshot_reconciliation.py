import sqlite3
import sys
import os

import pandas as pd


def load_snapshot_data(db_path: str = "crm.db") -> pd.DataFrame:
    con = sqlite3.connect(db_path)
    try:
        query = """
            SELECT
                c.id_canon,
                s.client_id,
                s.fund_number,
                s.fund_code,
                s.fund_name,
                s.snapshot_date,
                s.amount,
                s.source,
                s.company
            FROM snapshot s
            JOIN client c ON s.client_id = c.id
            WHERE s.is_active = 1
            ORDER BY c.id_canon, s.fund_number, s.snapshot_date
        """
        df = pd.read_sql_query(query, con)
    finally:
        con.close()
    return df


def detect_jumps(df: pd.DataFrame, pct_threshold: float = 0.5, abs_threshold: float = 50000.0):
    anomalies = []
    if df.empty:
        return anomalies

    group_cols = ["id_canon", "fund_number"]

    for (id_canon, fund_number), group in df.groupby(group_cols):
        group_sorted = group.sort_values("snapshot_date")
        prev_amount = None
        prev_date = None
        prev_name = None

        for _, row in group_sorted.iterrows():
            amount = float(row["amount"])
            date_str = row["snapshot_date"]
            fund_name = row["fund_name"]

            if prev_amount is not None and prev_amount != 0:
                change = amount - prev_amount
                pct = change / prev_amount
                if abs(pct) >= pct_threshold or abs(change) >= abs_threshold:
                    anomalies.append(
                        {
                            "id_canon": id_canon,
                            "fund_number": fund_number,
                            "fund_name": fund_name,
                            "prev_date": prev_date,
                            "prev_amount": prev_amount,
                            "curr_date": date_str,
                            "curr_amount": amount,
                            "change": change,
                            "pct_change": pct,
                        }
                    )

            prev_amount = amount
            prev_date = date_str
            prev_name = fund_name

    return anomalies


def summarize_single_source_clients(df: pd.DataFrame):
    """Return a non-destructive summary of clients that appear in only one source.

    This does not assume that being in a single source הוא בעיה,
    אבל עוזר לזהות לקוחות שלא מופיעים בכלל במקורות אחרים.
    """
    if df.empty or "source" not in df.columns:
        return None

    # Compute distinct sources per client
    client_sources = df.groupby("id_canon")["source"].nunique()
    single_source_clients = client_sources[client_sources == 1]

    if single_source_clients.empty:
        return None

    # Count by which source
    # Use a small aggregated frame: one row per client with its single source
    single_df = (
        df[df["id_canon"].isin(single_source_clients.index)]
        .groupby(["id_canon"])
        ["source"]
        .first()
        .reset_index()
    )

    by_source = single_df["source"].value_counts().to_dict()

    # Sample a few clients per source for display
    samples = {}
    max_per_source = 5
    for src in single_df["source"].unique():
        ids = (
            single_df[single_df["source"] == src]["id_canon"]
            .sort_values()
            .head(max_per_source)
            .tolist()
        )
        samples[src] = ids

    return {"total_single_source_clients": int(len(single_df)), "by_source": by_source, "samples": samples}


def main() -> int:
    db_path = os.environ.get("CRM_DB", "crm.db")
    df = load_snapshot_data(db_path)

    if df.empty:
        print("No snapshot data found in database")
        return 0

    anomalies = detect_jumps(df)

    if anomalies:
        print(
            f"Found {len(anomalies)} potential jumps (>=50% change or >=50,000 absolute change)."
        )

        max_print = 100
        for idx, a in enumerate(anomalies):
            if idx >= max_print:
                break
            pct_str = f"{a['pct_change'] * 100:.1f}%"
            print(
                "Client",
                a["id_canon"],
                "fund",
                a["fund_number"],
                f"({a['fund_name']})",
                "from",
                a["prev_date"],
                "=",
                a["prev_amount"],
                "to",
                a["curr_date"],
                "=",
                a["curr_amount"],
                "change=",
                a["change"],
                "(",
                pct_str,
                ")",
            )

        if len(anomalies) > max_print:
            print(f"... {len(anomalies) - max_print} more anomalies not shown")
    else:
        print("No significant month-to-month jumps detected")

    # Summarize clients that appear in only one source
    single_source_summary = summarize_single_source_clients(df)
    if single_source_summary:
        print()
        print(
            f"Clients that appear in only one source (non-destructive diagnostic): "
            f"{single_source_summary['total_single_source_clients']}"
        )
        print("Breakdown by source:")
        for src, count in single_source_summary["by_source"].items():
            print(f"  {src}: {count} clients")

        print("\nSample client IDs per source:")
        for src, ids in single_source_summary["samples"].items():
            print(f"  {src}: {', '.join(ids)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
