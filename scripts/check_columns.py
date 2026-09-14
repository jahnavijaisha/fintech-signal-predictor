import pandas as pd

candidates = pd.read_csv("data/raw/cfo_mention_8k.csv", dtype=str)
full_filings = pd.read_csv("data/raw/all_8k_filings.csv", dtype=str)

print("=== cfo_mention_8k.csv ===")
print(candidates.columns.tolist())
print(candidates.head(2))
print()
print("=== all_8k_filings.csv ===")
print(full_filings.columns.tolist())
print(full_filings.head(2))