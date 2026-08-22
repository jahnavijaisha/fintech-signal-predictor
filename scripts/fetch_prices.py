import sqlite3
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

FILING_DATE = "2026-07-29"
TICKER = "VFC"
BENCHMARK = "SPY"
DB_PATH = "data/filings.db"

def fetch_prices(ticker, start, end):
    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    df = df[["Close"]].rename(columns={"Close": "adj_close"})
df["adj_close"] = df["adj_close"].astype(float)
    df.index.name = "date"
    return df

def main():
    event_dt = datetime.strptime(FILING_DATE, "%Y-%m-%d")
    start = (event_dt - timedelta(days=10)).strftime("%Y-%m-%d")
    end = (event_dt + timedelta(days=10)).strftime("%Y-%m-%d")

    vfc = fetch_prices(TICKER, start, end)
    spy = fetch_prices(BENCHMARK, start, end)

    conn = sqlite3.connect(DB_PATH)
    for ticker, df in [(TICKER, vfc), (BENCHMARK, spy)]:
        (ticker, date.strftime("%Y-%m-%d"), float(row["adj_close"].iloc[0]) if hasattr(row["adj_close"], "iloc") else float(row["adj_close"]))
            conn.execute(
                "INSERT OR REPLACE INTO prices (ticker, date, adj_close) VALUES (?, ?, ?)",
                (ticker, date.strftime("%Y-%m-%d"), float(row["adj_close"]))
            )
    conn.commit()
    conn.close()
    print(f"Inserted {len(vfc)} {TICKER} rows and {len(spy)} {BENCHMARK} rows.")

if __name__ == "__main__":
    main()