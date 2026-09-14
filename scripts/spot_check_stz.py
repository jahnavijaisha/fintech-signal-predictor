"""
Quick spot-check: inspect STZ's CFO-departure matches for false positives.
"""

import pandas as pd

df = pd.read_csv("data/raw/confirmed_cfo_departures.csv", dtype={"cik_padded": str})
stz = df[df["ticker"] == "STZ"].copy()

print(f"STZ total rows: {len(stz)}")
print("\nmatched_phrase breakdown:")
print(stz["matched_phrase"].value_counts())

print("\nDate range:")
print(f"  {stz['file_date'].min()} to {stz['file_date'].max()}")

print("\nSample of 10 accession numbers + dates + matched phrase:")
print(stz[["accession_no", "file_date", "matched_phrase"]].head(10).to_string(index=False))