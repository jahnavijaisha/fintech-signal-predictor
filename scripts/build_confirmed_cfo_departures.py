import pandas as pd

candidates = pd.read_csv("data/raw/cfo_mention_8k.csv", dtype=str)
full_filings = pd.read_csv("data/raw/all_8k_filings_full.csv", dtype=str)

# Normalize accession numbers (strip dashes) so formatting differences don't break the merge
candidates["accession_norm"] = candidates["accession_no"].str.replace("-", "", regex=False)
full_filings["accession_norm"] = full_filings["accessionNumber"].str.replace("-", "", regex=False)

# Merge candidates against full filing list to pull in filingDate, primaryDocument, etc.
merged = candidates.merge(
    full_filings[["accession_norm", "filingDate", "primaryDocument", "form"]],
    on="accession_norm",
    how="left",
    suffixes=("", "_full")
)

# Sanity check: how many candidates failed to find a match at all?
unmatched = merged[merged["filingDate"].isna()]
print(f"Total candidates: {len(candidates)}")
print(f"Matched: {len(merged) - len(unmatched)}")
print(f"Unmatched: {len(unmatched)}")

# Check form type agreement (form from cfo_mention_8k.csv vs form from all_8k_filings.csv)
mismatched_form = merged[merged["form"] != merged["form_full"]]
print(f"Form mismatches between the two sources: {len(mismatched_form)}")

# Any candidate with no match here has no plain 8-K on record (likely only an 8-K/A exists)
confirmed = merged[merged["filingDate"].notna()].copy()
no_plain_8k = merged[merged["filingDate"].isna()]

print(f"Confirmed 8-K (non-amendment): {len(confirmed)}")
print(f"No matching plain 8-K found (likely 8-K/A only): {len(no_plain_8k)}")

confirmed.to_csv("data/raw/confirmed_cfo_departures.csv", index=False)
print("Saved to data/raw/confirmed_cfo_departures.csv")