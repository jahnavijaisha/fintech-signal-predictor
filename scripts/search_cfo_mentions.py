import pandas as pd
import requests
import time
import os

HEADERS = {"User-Agent": "Jaanu Personal Project jahna@example.com"}  # your real email

INPUT_PATH = "data/reference/sp500_ciks.csv"
OUTPUT_PATH = "data/raw/cfo_mention_8k.csv"
SLEEP_SECONDS = 0.15
SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
DEPARTURE_PHRASES = ["resignation", "resigned", "stepping down", "termination of employment", "will depart"]

def search_cfo_mentions(cik_padded, departure_phrase):
    """Search a company's 8-Ks for filings mentioning CFO + a departure-related phrase."""
    all_hits = []
    from_offset = 0
    query = f'"Chief Financial Officer" "{departure_phrase}"'

    while True:
        params = {
            "q": query,
            "forms": "8-K",
            "ciks": cik_padded,
            "from": from_offset,
        }

        resp = None
        for attempt in range(3):
            try:
                resp = requests.get(SEARCH_URL, headers=HEADERS, params=params, timeout=15)
                break
            except requests.exceptions.RequestException as e:
                print(f"  Request error for CIK {cik_padded}: {e}, retrying ({attempt + 1}/3)...")
                time.sleep(3)

        if resp is None:
            print(f"  Gave up on CIK {cik_padded} after 3 retries")
            return all_hits

        if resp.status_code != 200:
            print(f"  Failed search: status {resp.status_code} for CIK {cik_padded}")
            return all_hits

        data = resp.json()
        hits = data.get("hits", {}).get("hits", [])
        total = data.get("hits", {}).get("total", {}).get("value", 0)

        if not hits:
            break

        all_hits.extend(hits)
        from_offset += len(hits)

        if from_offset >= total:
            break

        time.sleep(SLEEP_SECONDS)

    return all_hits


def main():
    os.makedirs("data/raw", exist_ok=True)
    companies = pd.read_csv(INPUT_PATH, dtype={"cik_padded": str})

    records = []

    for i, row in companies.iterrows():
        ticker = row["ticker"]
        cik_padded = row["cik_padded"]

        if pd.isna(cik_padded):
            continue

        for phrase in DEPARTURE_PHRASES:
            hits = search_cfo_mentions(cik_padded, phrase)

            for hit in hits:
                source = hit.get("_source", {})
                records.append({
                    "ticker": ticker,
                    "cik_padded": cik_padded,
                    "accession_no": hit.get("_id", "").split(":")[0],
                    "file_date": source.get("file_date"),
                    "form": source.get("form"),
                    "matched_phrase": phrase,
                })

            time.sleep(SLEEP_SECONDS)

        if (i + 1) % 50 == 0:
            print(f"Processed {i + 1}/{len(companies)} companies...")
            pd.DataFrame(records).drop_duplicates(subset=["accession_no"]).to_csv(OUTPUT_PATH, index=False)

    result = pd.DataFrame(records)

    before = len(result)
    result = result.drop_duplicates(subset=["accession_no"])
    after = len(result)

    result.to_csv(OUTPUT_PATH, index=False)
    print(f"\nDone. Saved {after} CFO-departure-candidate 8-K filings to {OUTPUT_PATH}")
    if before != after:
        print(f"(Removed {before - after} duplicate rows across phrase searches)")

    print(result["ticker"].value_counts().head(10))
if __name__ == "__main__":
    main()