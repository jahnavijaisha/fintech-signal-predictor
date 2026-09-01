"""
Pulls the FULL 8-K filing history per company, including paginated
filings beyond the 'recent' window in the submissions API.
"""
import time
import pandas as pd
import requests

SEC_USER_AGENT = "T Jahnavi Jaisha   jahnavitulluru8@gmail.com"
HEADERS = {"User-Agent": "Jahnavi Jaisha jahnavitulluru8@gmail.com"}
REQUEST_DELAY = 0.15


def fetch_json(url):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_all_filings_for_cik(cik_padded: str) -> list[dict]:
    """Returns a list of filing dicts (form, filingDate, accessionNumber, primaryDocument)
    across BOTH the 'recent' block and any paginated 'files' entries."""
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    data = fetch_json(url)
    time.sleep(REQUEST_DELAY)

    all_rows = []

    def rows_from_block(block):
        forms = block["form"]
        dates = block["filingDate"]
        accs = block["accessionNumber"]
        docs = block["primaryDocument"]
        return [
            {"form": forms[i], "filingDate": dates[i],
             "accessionNumber": accs[i], "primaryDocument": docs[i]}
            for i in range(len(forms))
        ]

    all_rows.extend(rows_from_block(data["filings"]["recent"]))

    # Walk paginated older filings, if any
    for file_entry in data["filings"].get("files", []):
        page_url = f"https://data.sec.gov/submissions/{file_entry['name']}"
        page_data = fetch_json(page_url)
        time.sleep(REQUEST_DELAY)
        all_rows.extend(rows_from_block(page_data))

    return all_rows


def main():
    # Reuse your existing ticker/CIK list from Step 6a
    tickers_df = pd.read_csv("data/reference/sp500_ciks.csv", dtype={"cik_padded": str})

    all_filings = []
    for i, row in tickers_df.iterrows():
        cik_padded = row["cik_padded"]
        try:
            filings = get_all_filings_for_cik(cik_padded)
        except requests.RequestException as e:
            print(f"[{i}] {row['ticker']}: failed ({e}), skipping")
            continue

        eight_ks = [f for f in filings if f["form"] == "8-K"]
        for f in eight_ks:
            f["ticker"] = row["ticker"]
            f["cik_padded"] = cik_padded
        all_filings.extend(eight_ks)

        if i % 10 == 0:
            print(f"[{i}/{len(tickers_df)}] {row['ticker']}: {len(eight_ks)} 8-Ks (running total: {len(all_filings)})")

    out_df = pd.DataFrame(all_filings)
    out_df.to_csv("data/raw/all_8k_filings_full.csv", index=False)
    print(f"Done. {len(out_df)} total 8-K filings saved.")


if __name__ == "__main__":
    main()