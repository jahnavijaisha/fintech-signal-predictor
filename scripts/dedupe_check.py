import pandas as pd

df = pd.read_csv("data/raw/confirmed_cfo_departures.csv", dtype=str)

print(f"Total rows: {len(df)}")

dupe_accn = df[df.duplicated(subset=["accession_no"], keep=False)]
print(f"\nDuplicate accession_no rows: {len(dupe_accn)}")
if len(dupe_accn) > 0:
    print(dupe_accn.sort_values("accession_no").to_string())

if "ticker" in df.columns and "filing_date" in df.columns:
    dupe_event = df[df.duplicated(subset=["ticker", "filing_date"], keep=False)]
    print(f"\nDuplicate (ticker, filing_date) rows: {len(dupe_event)}")
    if len(dupe_event) > 0:
        print(dupe_event.sort_values(["ticker", "filing_date"]).to_string())
else:
    print("\n[!] Columns ticker/filing_date not found. Actual columns:")
    print(list(df.columns))

dupe_full = df[df.duplicated(keep=False)]
print(f"\nFully identical duplicate rows: {len(dupe_full)}")

print("\nDone.")