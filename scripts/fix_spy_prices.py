"""
Fix SPY: the prices table only had 15 SPY rows from the Step 5 VFC pilot,
which caused batch_pull_prices.py's "already present" check to wrongly skip
pulling the full 2001-2026 SPY range needed for the batch of 506 events.
"""

import sqlite3
import pandas as pd
import yfinance as yf

DB_PATH = "data/filings.db"
PLAN_PATH = "data/raw/price_pull_plan.csv"

def main():
    plan = pd.read_csv(PLAN_PATH)
    overall_start = plan["pull_start"].min()
    overall_end = plan["pull_end"].max()
    print(f"Pulling full SPY range: {overall_start} to {overall_end}")

    end_padded = (pd.to_datetime(overall_end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    hist = yf.download("SPY", start=overall_start, end=end_padded, progress=False, auto_adjust=False)

    rows = []
    for date, row in hist.iterrows():
        adj_close = row["Adj Close"]
        if hasattr(adj_close, "item"):
            adj_close = adj_close.item()
        rows.append(("SPY", date.strftime("%Y-%m-%d"), float(adj_close)))

    conn = sqlite3.connect(DB_PATH)
    conn.executemany(
        "INSERT OR IGNORE INTO prices (ticker, date, adj_close) VALUES (?, ?, ?)",
        rows
    )
    conn.commit()

    total_spy = conn.execute("SELECT COUNT(*) FROM prices WHERE ticker = 'SPY'").fetchone()[0]
    print(f"SPY rows fetched this run: {len(rows)}")
    print(f"Total SPY rows in DB now: {total_spy}")
    conn.close()

if __name__ == "__main__":
    main()