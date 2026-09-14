import pandas as pd

candidates = pd.read_csv("data/raw/cfo_mention_8k.csv", dtype=str)
full_filings = pd.read_csv("data/raw/all_8k_filings.csv", dtype=str)

print(f"all_8k_filings.csv row count: {len(full_filings)}")
print(f"Expected ~155,039 if pull_8k_filings_full.py output is what's currently in the file")
print()

# Show raw accession number samples from both files, unmodified
print("Sample accession_no from cfo_mention_8k.csv:")
print(candidates["accession_no"].head(5).tolist())
print()
print("Sample accessionNumber from all_8k_filings.csv:")
print(full_filings["accessionNumber"].head(5).tolist())
print()

# Check one specific unmatched candidate manually
candidates["accession_norm"] = candidates["accession_no"].str.replace("-", "", regex=False)
full_filings["accession_norm"] = full_filings["accessionNumber"].str.replace("-", "", regex=False)

sample_unmatched = candidates.iloc[0]
print(f"Looking for candidate: ticker={sample_unmatched['ticker']}, cik={sample_unmatched['cik_padded']}, accession_norm={sample_unmatched['accession_norm']}")
match_in_full = full_filings[full_filings["accession_norm"] == sample_unmatched["accession_norm"]]
print(f"Found {len(match_in_full)} match(es) in all_8k_filings.csv for this accession number")

# How many unique CIKs are in each file, to check coverage
print()
print(f"Unique CIKs in cfo_mention_8k.csv: {candidates['cik_padded'].nunique()}")
print(f"Unique CIKs in all_8k_filings.csv: {full_filings['cik_padded'].nunique()}")