"""
Spot-check additional tickers to see if the false-positive pattern from STZ
generalizes: check MGM (another high-count outlier) plus a couple of
typical/low-count tickers for contrast.
"""

import pandas as pd
import requests
import time
import re

HEADERS = {"User-Agent": "Jaanu Research jaanu@example.com"}  # match your working UA

df = pd.read_csv("data/raw/confirmed_cfo_departures.csv", dtype={"cik_padded": str})

# pick MGM (high count) + 2 tickers with low filing counts, for contrast
counts = df["ticker"].value_counts()
low_count_tickers = counts[counts <= 3].sample(n=2, random_state=1).index.tolist()
tickers_to_check = ["MGM"] + low_count_tickers

print(f"Checking tickers: {tickers_to_check}\n")

for ticker in tickers_to_check:
    sub = df[df["ticker"] == ticker]
    sample = sub.sample(n=min(3, len(sub)), random_state=42)

    for _, row in sample.iterrows():
        cik = row["cik_padded"]
        accession_no = row["accession_no"]
        accession_nodash = accession_no.replace("-", "")
        primary_doc = row["primaryDocument"]

        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_nodash}/{primary_doc}"
        print(f"\n{'='*80}\n{ticker} | {accession_no} ({row['file_date']}) — matched: {row['matched_phrase']}\nURL: {url}")

        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            text = resp.text
            text_clean = re.sub(r"<[^>]+>", " ", text)
            text_clean = re.sub(r"\s+", " ", text_clean)

            idx = text_clean.lower().find("chief financial officer")
            if idx == -1:
                print("  'Chief Financial Officer' not found in document text.")
            else:
                snippet = text_clean[max(0, idx-200):idx+300]
                print(f"  Context:\n  ...{snippet}...")

        except Exception as e:
            print(f"  Failed to fetch: {e}")

        time.sleep(0.5)