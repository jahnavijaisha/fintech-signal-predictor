"""
Retry the 4 failed tickers from batch_pull_prices.py with corrections,
and flag genuine no-data cases for exclusion rather than retry.
"""

import sqlite3
import pandas as pd
import yfinance as yf

DB_PATH = "data/filings.db"

TICKER_FIXES = {
    "BRK.B": "BRK-B",
}

KNOWN_UNRESOLVABLE = ["CHTR", "DAL"]

def check_original_filing_dates():
    verified = pd.read_csv("data/raw/verified_cfo_departures.csv", dtype={"cik_padded": str})
    is_verified = verified["verified"].astype(str).str.strip().str.lower() == "true"
    verified = verified[is_verified]

    for ticker in ["CHTR", "DAL", "VICI"]:
        rows = verified[verified["ticker"] == ticker]
        print(f"\n{ticker} verified filing date(s):")
        print(rows[["file_date", "matched_phrase"]].to_string(index=False))

def retry_fixed_ticker(conn, yahoo_ticker, plan_ticker, start, end):
    end_padded = (pd.to_datetime(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    hist = yf.download(yahoo_ticker, start=start, end=end_padded, progress=False, auto_adjust=False)
    if hist.empty:
        print(f"  still no data for {yahoo_ticker}")
        return 0

    rows = []
    for date, row in hist.iterrows():
        adj_close = row["Adj Close"]
        if hasattr(adj_close, "item"):
            adj_close = adj_close.item()
        rows.append((plan_ticker, date.strftime("%Y-%m-%d"), float(adj_close)))

    conn.executemany(
        "INSERT OR IGNORE INTO prices (ticker, date, adj_close) VALUES (?, ?, ?)",
        rows
    )
    conn.commit()
    return len(rows)

def retry_vici_narrow(conn):
    hist = yf.download("VICI", start="2017-10-06", end="2017-10-22", progress=False, auto_adjust=False)
    if hist.empty:
        print("Still no data for VICI even post-IPO — leave unresolved")
        return

    rows = []
    for date, row in hist.iterrows():
        adj_close = row["Adj Close"]
        if hasattr(adj_close, "item"):
            adj_close = adj_close.item()
        rows.append(("VICI", date.strftime("%Y-%m-%d"), float(adj_close)))

    conn.executemany(
        "INSERT OR IGNORE INTO prices (ticker, date, adj_close) VALUES (?, ?, ?)",
        rows
    )
    conn.commit()
    print(f"Inserted {len(rows)} VICI rows (2017-10-06 onward)")

def main():
    check_original_filing_dates()

    plan = pd.read_csv("data/raw/price_pull_plan.csv")
    failures = pd.read_csv("data/raw/price_pull_failures.csv")
    conn = sqlite3.connect(DB_PATH)

    for _, row in failures.iterrows():
        ticker = row["ticker"]
        if ticker in TICKER_FIXES:
            yahoo_ticker = TICKER_FIXES[ticker]
            plan_row = plan[plan["ticker"] == ticker].iloc[0]
            print(f"\nRetrying {ticker} as {yahoo_ticker}...")
            n = retry_fixed_ticker(conn, yahoo_ticker, ticker, plan_row["pull_start"], plan_row["pull_end"])
            print(f"  inserted {n} rows")
        elif ticker in KNOWN_UNRESOLVABLE:
            print(f"\n{ticker}: leaving unresolved — see filing-date check above")
        elif ticker == "VICI":
            print(f"\n{ticker}: retrying with narrow post-IPO window...")
            retry_vici_narrow(conn)

    conn.close()

if __name__ == "__main__":
    main()