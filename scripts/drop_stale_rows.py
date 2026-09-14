"""
One-off cleanup: verified_cfo_departures.csv currently contains 1544 rows
verified BEFORE the exhibit-type fix (searched the whole submission,
including EX-3.x/EX-10.x) followed by 9132 rows verified AFTER the fix.
This drops the first 1544 stale rows so a rerun of verify_cfo_departures.py
only reprocesses those, instead of all 10,676.
"""

import pandas as pd

PATH = "data/raw/verified_cfo_departures.csv"
STALE_ROW_COUNT = 1544

df = pd.read_csv(PATH)
print(f"Loaded {len(df)} rows.")

if len(df) <= STALE_ROW_COUNT:
    raise SystemExit(
        f"File only has {len(df)} rows, which is <= STALE_ROW_COUNT ({STALE_ROW_COUNT}). "
        "Nothing to drop — check you're pointed at the right file before rerunning."
    )

stale = df.iloc[:STALE_ROW_COUNT]
fresh = df.iloc[STALE_ROW_COUNT:]

stale.to_csv("data/raw/verified_cfo_departures_stale_backup.csv", index=False)
fresh.to_csv(PATH, index=False)

print(f"Backed up {len(stale)} stale rows to data/raw/verified_cfo_departures_stale_backup.csv")
print(f"Kept {len(fresh)} fresh (post-fix) rows in {PATH}")
print("Now rerun verify_cfo_departures.py — it will reprocess only the stale accessions.")