"""
Step 6f-3: Loop all verified CFO-departure filings, compute 3-day
market-adjusted abnormal return vs SPY, and label Positive/Negative/Neutral —
same methodology as compute_label.py's VFC pilot, applied at scale.
"""

import sqlite3
import pandas as pd
from bisect import bisect_left

DB_PATH = "data/filings.db"
VERIFIED_PATH = "data/raw/verified_cfo_departures.csv"
BENCHMARK = "SPY"
THRESHOLD = 0.005  # same as VFC pilot — tune later
WINDOW_LEN = 3      # filing date + next 2 trading days

FAILURES_LOG = "data/raw/label_compute_failures.csv"

def get_prices(conn, ticker):
    rows = conn.execute(
        "SELECT date, adj_close FROM prices WHERE ticker = ? ORDER BY date",
        (ticker,)
    ).fetchall()
    return {date: adj_close for date, adj_close in rows}, [r[0] for r in rows]

def find_event_start(dates_sorted, file_date):
    """First trading date >= file_date (handles weekend/holiday filings)."""
    i = bisect_left(dates_sorted, file_date)
    if i == len(dates_sorted):
        return None
    return i

def ensure_filing_row(conn, row):
    """Insert into filings if this accession_no isn't already present."""
    exists = conn.execute(
        "SELECT 1 FROM filings WHERE accession_no = ?", (row["accession_no"],)
    ).fetchone()
    if exists:
        return
    conn.execute(
        """INSERT INTO filings (accession_no, cik, ticker, filing_date, item_codes, is_confounded, raw_path)
           VALUES (?, ?, ?, ?, ?, 0, '')""",
        (row["accession_no"], row["cik_padded"], row["ticker"], row["file_date"], "5.02")
    )

def main():
    verified = pd.read_csv(VERIFIED_PATH, dtype={"cik_padded": str})
    is_verified = verified["verified"].astype(str).str.strip().str.lower() == "true"
    verified = verified[is_verified].copy()
    print(f"Processing {len(verified)} verified filings")

    conn = sqlite3.connect(DB_PATH)
    spy_prices, spy_dates_sorted = get_prices(conn, BENCHMARK)

    labels = []
    failures = []
    price_cache = {}

    for _, row in verified.iterrows():
        ticker = row["ticker"]
        file_date = row["file_date"]

        if ticker not in price_cache:
            price_cache[ticker] = get_prices(conn, ticker)
        ticker_prices, ticker_dates = price_cache[ticker]

        if not ticker_prices:
            failures.append({"accession_no": row["accession_no"], "ticker": ticker,
                              "file_date": file_date, "reason": "no price data for ticker"})
            continue

        common_dates = sorted(set(ticker_prices.keys()) & set(spy_prices.keys()))
        start_i = find_event_start(common_dates, file_date)
        if start_i is None or start_i + WINDOW_LEN > len(common_dates):
            failures.append({"accession_no": row["accession_no"], "ticker": ticker,
                              "file_date": file_date, "reason": "insufficient trading days in window"})
            continue

        window_dates = common_dates[start_i: start_i + WINDOW_LEN]

        abnormal_return = 0.0
        for i in range(1, len(window_dates)):
            d0, d1 = window_dates[i - 1], window_dates[i]
            t_ret = (ticker_prices[d1] - ticker_prices[d0]) / ticker_prices[d0]
            s_ret = (spy_prices[d1] - spy_prices[d0]) / spy_prices[d0]
            abnormal_return += (t_ret - s_ret)

        if abnormal_return > THRESHOLD:
            label = "Positive"
        elif abnormal_return < -THRESHOLD:
            label = "Negative"
        else:
            label = "Neutral"

        ensure_filing_row(conn, row)
        conn.execute(
            "UPDATE filings SET abnormal_return = ?, label = ? WHERE accession_no = ?",
            (abnormal_return, label, row["accession_no"])
        )

        labels.append({"accession_no": row["accession_no"], "ticker": ticker,
                        "file_date": file_date, "abnormal_return": abnormal_return, "label": label})

    conn.commit()
    conn.close()

    labels_df = pd.DataFrame(labels)
    print(f"\nLabeled {len(labels_df)} of {len(verified)} filings")
    if failures:
        pd.DataFrame(failures).to_csv(FAILURES_LOG, index=False)
        print(f"{len(failures)} failures logged to {FAILURES_LOG}")

    if not labels_df.empty:
        print("\nLabel distribution:")
        print(labels_df["label"].value_counts())
        print("\nAs fractions:")
        print((labels_df["label"].value_counts(normalize=True) * 100).round(1))

if __name__ == "__main__":
    main()