"""
Investigate multi-document theory: for a 'not found' accession, list all
files in the accession folder (via index.json) and check each one for
'Chief Financial Officer' and the matched departure phrase.
"""

import requests
import time
import re

HEADERS = {"User-Agent": "Jaanu Research jaanu@example.com"}  # match your working UA

# MGM, accession 0001193125-15-105141, cik 789570
CIK = 789570
ACCESSION_NO = "0001193125-15-105141"
ACCESSION_NODASH = ACCESSION_NO.replace("-", "")

index_url = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{ACCESSION_NODASH}/index.json"
print(f"Fetching manifest: {index_url}")

resp = requests.get(index_url, headers=HEADERS, timeout=10)
data = resp.json()

files = data.get("directory", {}).get("item", [])
print(f"\nFound {len(files)} files in this accession:")
for f in files:
    print(f"  {f['name']}  ({f.get('type', 'unknown type')}, {f.get('size', '?')} bytes)")

print(f"\n{'='*80}\nSearching each file for 'Chief Financial Officer' and 'resignation'...\n")

for f in files:
    fname = f["name"]
    file_url = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{ACCESSION_NODASH}/{fname}"
    try:
        r = requests.get(file_url, headers=HEADERS, timeout=10)
        text = re.sub(r"<[^>]+>", " ", r.text)
        text = re.sub(r"\s+", " ", text)

        has_cfo = "chief financial officer" in text.lower()
        has_phrase = "resignation" in text.lower()

        print(f"{fname}: CFO mention = {has_cfo}, 'resignation' = {has_phrase}")

        if has_cfo and has_phrase:
            idx = text.lower().find("chief financial officer")
            print(f"  --> Context: ...{text[max(0,idx-150):idx+250]}...")

    except Exception as e:
        print(f"{fname}: failed to fetch ({e})")

    time.sleep(0.3)