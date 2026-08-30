import pandas as pd
import requests
import time
import os

HEADERS = {"User-Agent": "jahnavitulluru8@gmail.com"}  # use your real email

INPUT_PATH = "data/reference/sp500_ciks.csv"
OUTPUT_PATH = "data/raw/all_8k_filings.csv"
SLEEP_SECONDS = 0.15  # stay under SEC's 10 requests/second limit


def get_filing_history(cik_padded):
    """Fetch a company's filing history from SEC submissions API and return only 8-Ks."""
    cik_padded = str(cik_padded).zfill(10)  # defensive re-pad in case leading zeros were lost
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    resp = requests.get(url, headers=HEADERS)
    

    if resp.status_code != 200:
        print(f"  Failed request: status {resp.status_code} for {url}")
        return None

    data = resp.json()
    recent = data.get("filings", {}).get("recent", {})

    df = pd.DataFrame({
        "form": recent.get("form", []),
        "filingDate": recent.get("filingDate", []),
        "accessionNumber": recent.get("accessionNumber", []),
        "primaryDocument": recent.get("primaryDocument", []),
    })

    return df[df["form"] == "8-K"]


def main():
    os.makedirs("data/raw", exist_ok=True)
    companies = pd.read_csv(INPUT_PATH, dtype={"cik_padded": str})

    all_filings = []
    failed = []

    for i, row in companies.iterrows():
        ticker = row["ticker"]
        cik_padded = row["cik_padded"]

        if pd.isna(cik_padded):
            continue

        filings = get_filing_history(cik_padded)

        if filings is None:
            failed.append(ticker)
        elif len(filings) > 0:
            filings = filings.copy()
            filings["ticker"] = ticker
            filings["cik_padded"] = cik_padded
            all_filings.append(filings)

        # simple progress indicator every 50 companies
        if (i + 1) % 50 == 0:
            print(f"Processed {i + 1}/{len(companies)} companies...")

        time.sleep(SLEEP_SECONDS)

    result = pd.concat(all_filings, ignore_index=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"\nDone. Saved {len(result)} total 8-K filings to {OUTPUT_PATH}")
    print(f"Covered {len(companies) - len(failed)} / {len(companies)} companies")
    if failed:
        print(f"Failed for {len(failed)} tickers: {failed}")


if __name__ == "__main__":
    main()