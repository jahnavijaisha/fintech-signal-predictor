"""
Step 2 of STZ spot-check: fetch actual filing text for a sample of STZ
matches and inspect the context around 'Chief Financial Officer' and the
matched departure phrase, to see if they're describing the same event.
"""

import pandas as pd
import requests
import time
import re

HEADERS = {"User-Agent": "T Jahnavi Jaisha  jahnavitulluru8@gmail.com"}  # match whatever UA you used in fetch_filing.py

df = pd.read_csv("data/raw/confirmed_cfo_departures.csv", dtype={"cik_padded": str})
stz = df[df["ticker"] == "STZ"].copy()

# Sample 5 across different eras, not just the first 5
sample = stz.sample(n=5, random_state=42)

for _, row in sample.iterrows():
    cik = row["cik_padded"]
    accession_no = row["accession_no"]
    accession_nodash = accession_no.replace("-", "")
    primary_doc = row["primaryDocument"]

    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_nodash}/{primary_doc}"
    print(f"\n{'='*80}\n{accession_no} ({row['file_date']}) — matched: {row['matched_phrase']}\nURL: {url}")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        text = resp.text
        # crude tag strip for readability
        text_clean = re.sub(r"<[^>]+>", " ", text)
        text_clean = re.sub(r"\s+", " ", text_clean)

        # find index of "Chief Financial Officer" and print surrounding context
        idx = text_clean.lower().find("chief financial officer")
        if idx == -1:
            print("  'Chief Financial Officer' not found in document text (may be in an exhibit not fetched, or different casing).")
        else:
            snippet = text_clean[max(0, idx-200):idx+300]
            print(f"  Context around 'Chief Financial Officer':\n  ...{snippet}...")

    except Exception as e:
        print(f"  Failed to fetch: {e}")

    time.sleep(0.5)