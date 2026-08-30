import pandas as pd
import requests
import json
import os

# SEC requires a descriptive User-Agent identifying you
HEADERS = {"User-Agent": "jahnavitulluru8@gmail.com"}

OUTPUT_DIR = "data/reference"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "sp500_ciks.csv")


def get_sp500_tickers():
    """Pull current S&P 500 constituents from Wikipedia."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    wiki_headers = {"User-Agent": "Mozilla/5.0"}  # Wikipedia blocks requests with no browser-like UA
    resp = requests.get(url, headers=wiki_headers)
    resp.raise_for_status()

    from io import StringIO
    tables = pd.read_html(StringIO(resp.text))
    sp500_table = tables[0]  # first table on the page is the constituent list
    sp500_table = sp500_table.rename(columns={"Symbol": "ticker", "Security": "company_name"})
    return sp500_table[["ticker", "company_name"]]


def get_sec_ticker_cik_map():
    """Pull SEC's official ticker -> CIK mapping."""
    url = "https://www.sec.gov/files/company_tickers.json"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()

    # data is a dict of dicts like {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ...}
    records = list(data.values())
    df = pd.DataFrame(records)
    df = df.rename(columns={"cik_str": "cik", "ticker": "ticker", "title": "sec_company_name"})
    return df[["ticker", "cik"]]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    sp500 = get_sp500_tickers()
    sec_map = get_sec_ticker_cik_map()

    # SEC tickers sometimes differ slightly in formatting (e.g. BRK.B vs BRK-B) — normalize before joining
    sp500["ticker_clean"] = sp500["ticker"].str.replace(".", "-", regex=False)
    sec_map["ticker_clean"] = sec_map["ticker"].str.upper()

    merged = sp500.merge(sec_map, on="ticker_clean", how="left", suffixes=("", "_sec"))
    merged = merged[["ticker", "company_name", "cik"]]

    unmatched = merged[merged["cik"].isna()]
    if len(unmatched) > 0:
        print(f"Warning: {len(unmatched)} tickers could not be matched to a CIK:")
        print(unmatched["ticker"].tolist())

    # SEC CIKs need to be zero-padded to 10 digits for API calls later — store that format too
    merged["cik"] = merged["cik"].astype("Int64")
    merged["cik_padded"] = merged["cik"].apply(lambda x: str(x).zfill(10) if pd.notna(x) else None)

    merged.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved {len(merged)} companies to {OUTPUT_PATH}")
    print(f"Matched: {merged['cik'].notna().sum()} / {len(merged)}")


if __name__ == "__main__":
    main()