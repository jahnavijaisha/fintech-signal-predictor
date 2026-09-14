"""
Build data/raw/price_pull_plan.csv from VERIFIED CFO-departure filings only.
Supersedes the 6f-1 version, which grouped by the full unverified 10,676-row
candidate set (498 tickers). This version uses verified_cfo_departures.csv
(verified=True rows) instead, produced by the 6c-2/proximity rework.
"""

import pandas as pd
from pathlib import Path

VERIFIED_PATH = Path("data/raw/verified_cfo_departures.csv")
OUTPUT_PATH = Path("data/raw/price_pull_plan.csv")
BUFFER_DAYS = 10

def main():
    df = pd.read_csv(VERIFIED_PATH, dtype={"cik_padded": str})

    # 'verified' may load as bool or string depending on how it was written —
    # normalize defensively either way
    is_verified = df["verified"].astype(str).str.strip().str.lower() == "true"
    verified = df[is_verified].copy()
    print(f"Verified true positives: {len(verified)} rows out of {len(df)}")

    verified["file_date"] = pd.to_datetime(verified["file_date"])

    grouped = verified.groupby("ticker")["file_date"].agg(["min", "max"]).reset_index()
    grouped.columns = ["ticker", "earliest_filing", "latest_filing"]

    grouped["pull_start"] = (grouped["earliest_filing"] - pd.Timedelta(days=BUFFER_DAYS)).dt.strftime("%Y-%m-%d")
    grouped["pull_end"] = (grouped["latest_filing"] + pd.Timedelta(days=BUFFER_DAYS)).dt.strftime("%Y-%m-%d")

    result = grouped[["ticker", "pull_start", "pull_end"]]
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved {len(result)} unique tickers to {OUTPUT_PATH}")
    print(f"Overall pull range: {result['pull_start'].min()} to {result['pull_end'].max()}")

if __name__ == "__main__":
    main()