"""
Step 6f-2: Batch-pull ticker + SPY daily adjusted close prices for all
274 tickers in data/raw/price_pull_plan.csv, using the same yfinance +
prices-table approach as fetch_prices.py (Step 5), but looped and resumable.
"""

import sqlite3
import time
import pandas as pd
import yfinance as yf
from pathlib import Path

PLAN_PATH = Path("data/raw/price_pull_plan.csv")
DB_PATH = Path("data/filings.db")
FAILURES_PATH = Path("data/raw/price_pull_failures.csv")
SLEEP_SECONDS = 1.0  # be polite to Yahoo Finance between tickers

def get_existing_tickers(conn):
    """Tickers already fully present in the prices table, so reruns skip them."""
    rows = conn.execute("SELECT DISTINCT ticker FROM prices").fetchall()
    return {r[0] for r in rows}

def pull_and_insert(conn, ticker, start, end):
    # yfinance's 'end' is exclusive, so pad by a day to include the last date
    end_padded = (pd.to_datetime(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    hist = yf.download(ticker, start=start, end=end_padded, progress=False, auto_adjust=False)

    if hist.empty:
        raise ValueError("no data returned")

    rows = []
    for date, row in hist.iterrows():
        adj_close = row["Adj Close"]
        # yfinance sometimes returns a Series (MultiIndex columns) for single tickers
        if hasattr(adj_close, "item"):
            adj_close = adj_close.item()
        rows.append((ticker, date.strftime("%Y-%m-%d"), float(adj_close)))

    conn.executemany(
        "INSERT OR IGNORE INTO prices (ticker, date, adj_close) VALUES (?, ?, ?)",
        rows
    )
    conn.commit()
    return len(rows)

def main():
    plan = pd.read_csv(PLAN_PATH)
    conn = sqlite3.connect(DB_PATH)

    existing = get_existing_tickers(conn)
    failures = []

    # --- SPY: pull once over the full overall range, if not already done ---
    if "SPY" not in existing:
        overall_start = plan["pull_start"].min()
        overall_end = plan["pull_end"].max()
        print(f"Pulling SPY: {overall_start} to {overall_end}")
        try:
            n = pull_and_insert(conn, "SPY", overall_start, overall_end)
            print(f"  inserted {n} SPY rows")
        except Exception as e:
            print(f"  SPY FAILED: {e}")
            failures.append({"ticker": "SPY", "error": str(e)})
        time.sleep(SLEEP_SECONDS)
    else:
        print("SPY already present, skipping")

    # --- Per-ticker pulls ---
    remaining = plan[~plan["ticker"].isin(existing)]
    print(f"\n{len(remaining)} tickers left to pull (of {len(plan)} total)")

    for i, row in enumerate(remaining.itertuples(), start=1):
        print(f"[{i}/{len(remaining)}] {row.ticker}: {row.pull_start} to {row.pull_end}")
        try:
            n = pull_and_insert(conn, row.ticker, row.pull_start, row.pull_end)
            print(f"  inserted {n} rows")
        except Exception as e:
            print(f"  FAILED: {e}")
            failures.append({"ticker": row.ticker, "error": str(e)})
        time.sleep(SLEEP_SECONDS)

    conn.close()

    if failures:
        pd.DataFrame(failures).to_csv(FAILURES_PATH, index=False)
        print(f"\n{len(failures)} tickers failed, logged to {FAILURES_PATH}")
    else:
        print("\nAll tickers pulled successfully.")

if __name__ == "__main__":
    main()